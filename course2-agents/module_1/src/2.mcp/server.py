import json
import os
from typing import Annotated

import requests
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv
load_dotenv("/Users/azen/Desktop/llm/ZJU-Tutorial/.env")


mcp = FastMCP("More Tools Server", json_response=True)


@mcp.tool()
def get_weather(
    city: Annotated[str, "The name of the city to be queried"],
) -> str:
    """
    查询某个城市当前的天气信息。
    底层通过 https://wttr.in 的公开接口获取数据。
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

        result = {
            k: {field: data[k][0][field] for field in fields}
            for k, fields in key_selection.items()
        }
    except Exception as exc:  # noqa: BLE001
        result = {
            "error": "Error encountered while fetching weather data",
            "detail": str(exc),
        }

    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def search_info_by_tavily(
    query: Annotated[str, "用户想要搜索的内容"],
) -> str:
    """
    使用 Tavily 搜索 API 来搜索相关信息。
    需要在环境变量中配置 TAVILY_API_KEY。
    """

    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps(
            {
                "error": "TAVILY_API_KEY not set in environment",
            },
            ensure_ascii=False,
        )

    client = TavilyClient(api_key)
    response = client.search(query=query)
    return json.dumps(response, ensure_ascii=False)


if __name__ == "__main__":
    # 使用 stdio 作为传输方式，方便被本地 client 或 IDE 作为子进程启动
    mcp.run(transport="stdio")

