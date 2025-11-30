import os
import json
from typing import Dict, Any

import requests
from tavily import TavilyClient
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv
load_dotenv("/Users/azen/Desktop/llm/ZJU-Tutorial/.env")

# 创建 MCP Server 实例
mcp = FastMCP("mcp-server", json_response=False)


def _get_weather_impl(city: str) -> str:
    """
    实际的天气查询逻辑（同步实现，供 MCP 工具调用）
    """
    if not isinstance(city, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": [
            "temp_C",
            "FeelsLikeC",
            "humidity",
            "weatherDesc",
            "observation_time",
        ],
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


def _search_info_by_tavily_impl(query: str) -> str:
    """
    实际的 Tavily 搜索逻辑（同步实现，供 MCP 工具调用）
    """
    client = TavilyClient(os.getenv("TAVILY_API_KEY"))
    response = client.search(query=query)
    return json.dumps(response, ensure_ascii=False)


@mcp.tool()
def get_weather(city: str) -> str:
    """
    查询某个城市的天气，返回字符串化的 JSON 结果。
    参数:
        city: 城市名称，例如：深圳、北京、Shanghai 等
    """
    return _get_weather_impl(city)


@mcp.tool()
def search_info_by_tavily(query: str) -> str:
    """
    使用 Tavily 搜索相关信息，返回 JSON 字符串结果。
    参数:
        query: 用户想要搜索的内容
    """
    return _search_info_by_tavily_impl(query)


if __name__ == "__main__":
    # 使用 stdio 作为 MCP 传输层，方便本地 Agent 通过子进程连接
    mcp.run(transport="stdio")
