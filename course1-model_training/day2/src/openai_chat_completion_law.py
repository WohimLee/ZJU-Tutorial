
import argparse
from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"

messages = [
    {
        "role": "system",
        "content": (
            "你是一名中国刑法领域的法律助理。\n"
            "请基于【案件事实】和【可用法条】，按照“法律三段论”的方式进行推理，"
            "并给出【可能的罪名】及【法定刑罚区间】。\n\n"
            "【重要约束】\n"
            "- 不得编造法律条文\n"
            "- 不得给出具体刑期（如“判处三年六个月”）\n"
            "- 仅能在法条规定的刑罚区间内作出判断\n"
            "- 如存在不确定性，应明确说明\n\n"
            "【输出要求】\n"
            "请输出：适用法条、构成要件分析、罪名判断、法定刑罚区间（可用分段或JSON）。"
        )
    },
    {
        "role": "user",
        "content": (
            "【案件事实】\n"
            "经审理查明，2015年6月21日15时许，被告人白某某在大东区小河沿公交车站乘坐被害人张某某驾驶的133路公交车，"
            "当车辆行驶至沈阳市大东区东陵西路26号附近时，被告人白某某因未能下车而与司机张某某发生争执，"
            "并在该公交车行驶中用手拉拽档杆，被证人韩某某拉开后，"
            "被告人白某某又用手拉拽司机张某某的右胳膊，"
            "导致该车失控撞向右侧马路边停放的轿车和一个路灯杆，"
            "路灯杆折断后将福锅记炖品店的牌匾砸坏。\n\n"
            "经鉴定，本案损失价值共计人民币19,342.6元。\n\n"
            "【可用法条】\n"
            "《刑法》第一百一十四条：以危险方法危害公共安全，尚未造成严重后果的，"
            "处三年以上十年以下有期徒刑。"
        )
    }
]


def parse_args():
    parser = argparse.ArgumentParser(description="Client for vLLM API server")
    parser.add_argument(
        "--stream", default=True, help="Enable streaming response"
    )
    return parser.parse_args()


def main(args):
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=openai_api_key,
        base_url=openai_api_base,
    )

    models = client.models.list()
    model = models.data[0].id

    # Chat Completion API
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        stream=args.stream,
    )

    print("-" * 50)
    print("Chat completion results:")
    if args.stream:
        for chunk in chat_completion:
            print(chunk.choices[0].delta.content, end="", flush=True)
    else:
        print(chat_completion.choices[0].message.content)
    print("-" * 50)


if __name__ == "__main__":
    args = parse_args()
    main(args)