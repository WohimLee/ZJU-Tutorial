import os
import json
from typing import Annotated, Dict, Any, List

import requests
from openai import OpenAI

############################################
# 1. 初始化 LLM 客户端
############################################

llm_client = OpenAI(
    # 若没有配置环境变量，请改成：
    # api_key="sk-xxx",
    # base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("ALIBABA_API_KEY"),
    base_url=os.getenv("ALIBABA_API_URL"),
)

MODEL_NAME = "qwen3-max"

############################################
# 2. 工具函数定义
############################################

def get_weather(city: Annotated[str, 'The name of the city to be queried', True]):
    """
    查询指定城市天气。返回字符串化的结果。
    """
    if not isinstance(city, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }

    try:
        resp = requests.get(f"https://wttr.in/{city}?format=j1", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        ret: Dict[str, Any] = {}
        for k, fields in key_selection.items():
            if k in data and data[k]:
                ret[k] = {}
                for field in fields:
                    value = data[k][0].get(field)
                    # weatherDesc 是个 list
                    if field == "weatherDesc" and isinstance(value, list) and value:
                        value = value[0].get("value")
                    ret[k][field] = value

        return json.dumps(ret, ensure_ascii=False)
    except Exception as e:
        return f"Error encountered while fetching weather data: {e!r}"

def search_info_by_tavily(query):
    from tavily import TavilyClient
    client = TavilyClient(os.getenv("TAVILY_API_KEY"))
    response = client.search(
        query=query
    )
    return json.dumps(response, ensure_ascii=False)

############################################
# 3. 工具注册表 & tools 描述（给模型看的 schema）
############################################

TOOL_REGISTRY = {
    "get_weather": get_weather,
    "search_info_by_tavily": search_info_by_tavily,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询某个城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：深圳、北京、Shanghai 等",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_info_by_tavily",
            "description": "Tavily 搜索 API，搜索相关信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "用户想要搜索的内容"}
                },
                "required": ["query"],
            },
        },
    }
]

############################################
# 4. System 提示词（基础角色设定）
############################################

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "你是一个会主动使用工具的智能助手。"
        "当你需要查询实时信息、天气等时，请优先调用提供的工具。"
        "你可以多次调用工具，直到拿到足够信息后，再给出中文回答。"
    ),
}

############################################
# 5. Agent 主循环：自动多轮工具调用
############################################

def call_llm_with_tools(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    调一次 LLM，让它决定是否调用工具（tool_choice='auto'）。
    返回的是 message 对象（dict）。
    """
    response = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=history,
        tools=tools,
        tool_choice="auto",
        stream=False,
    )
    return response.choices[0].message


def run_agent_once(
    user_input: str,
    history: List[Dict[str, Any]],
    max_tool_rounds: int = 5,
) -> str:
    """
    针对一次用户输入，执行一个完整的 agent 流程：
    - 多轮工具调用（最多 max_tool_rounds 轮）
    - 最后使用 stream=True 做自然语言总结
    返回最终完整回复字符串。
    """

    # 先把用户输入 push 到 history
    history.append({"role": "user", "content": user_input})

    # 多轮工具调用循环
    for round_idx in range(max_tool_rounds):
        msg = call_llm_with_tools(history)

        # 先把本轮 assistant 消息加进历史（包括可能的 tool_calls）
        assistant_msg = {
            "role": "assistant",
            "content": msg.content,
        }
        if msg.tool_calls:
            assistant_msg["tool_calls"] = msg.tool_calls
        history.append(assistant_msg)

        # 如果没有 tool_calls，说明模型觉得自己已经可以直接回答，
        # 这里就结束工具循环，进入最终总结阶段。
        if not msg.tool_calls:
            break

        # 否则，执行每个工具调用
        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments or "{}"

            try:
                if isinstance(raw_args, str):
                    tool_args = json.loads(raw_args)
                else:
                    tool_args = raw_args
            except json.JSONDecodeError:
                tool_args = {}
            print("模型要求调用函数：", tool_name, "参数：", tool_args)
            func = TOOL_REGISTRY.get(tool_name)
            if func is None:
                tool_result = f"[工具 {tool_name} 未在本地注册]"
            else:
                try:
                    tool_result = func(**tool_args)
                except Exception as e:
                    tool_result = f"[调用工具 {tool_name} 出错: {e!r}]"

            # 把工具结果作为 role=tool 消息塞回去
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result),
                }
            )

        # 然后继续下一轮 for，看模型要不要再次发起 tool_calls

    # 工具阶段结束后，做一次“最终回答”，禁止继续调用工具
    final_answer = final_summarize(history)
    # 把最终自然语言回答也加入历史（方便多轮对话）
    history.append({"role": "assistant", "content": final_answer})
    return final_answer


############################################
# 6. 最终总结阶段（流式输出）
############################################

def final_summarize(history: List[Dict[str, Any]]) -> str:
    """
    使用流式输出的方式，在终端实时打印大模型最终回复。
    同时返回完整的回复字符串。
    注意这里 tool_choice='none'，不再允许调用工具。
    """
    print("助手：", end="", flush=True)

    stream = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=history,
        stream=True,
        tool_choice="none",  # 最终阶段禁止工具调用
        # 也可以不再传 tools；这里传不传都行
        # tools=tools,
    )

    full_content = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None) or ""
        if content:
            print(content, end="", flush=True)
            full_content += content
    print()  # 换行
    return full_content


############################################
# 7. 简单的对话入口
############################################

def truncate_history(history: List[Dict[str, Any]], max_messages: int = 30) -> List[Dict[str, Any]]:
    """
    简单的历史裁剪：只保留最近 max_messages 条消息（外加 system）。
    防止长时间对话导致上下文太长。
    """
    msgs = [m for m in history if m["role"] != "system"]
    if len(msgs) <= max_messages:
        return history

    # 保留 system + 最近 N 条非 system 消息
    new_history = [SYSTEM_MESSAGE] + msgs[-max_messages:]
    return new_history


def main():
    # 对话级别的 history（包含 system）
    history: List[Dict[str, Any]] = [SYSTEM_MESSAGE]

    print("已启动工具增强 Agent，对话中输入 exit / 退出 即可结束。")
    while True:
        user_input = input("用户：").strip()
        if user_input.lower() in {"exit", "quit", "q", "退出"}:
            print("再见 👋")
            break

        # 每轮前简单做一下历史截断
        history = truncate_history(history)

        try:
            _ = run_agent_once(user_input, history)
        except Exception as e:
            print(f"\n[调用出错]: {e!r}\n")


if __name__ == "__main__":
    main()
