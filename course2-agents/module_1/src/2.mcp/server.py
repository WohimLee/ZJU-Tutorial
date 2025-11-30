# server.py
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
import requests
import traceback

# 创建 MCP server，返回 JSON 结构结果更方便给 LLM 用
mcp = FastMCP("Weather Server", json_response=True)


@mcp.tool()
def get_weather(city: str) -> Dict[str, Any]:
    """
    根据城市名称获取当前天气信息。
    """
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
        ret = {
            k: {field: data[k][0][field] for field in fields}
            for k, fields in key_selection.items()
        }
        return ret
    except Exception:
        return {
            "error": "Error encountered while fetching weather data",
            "traceback": traceback.format_exc(),
        }


if __name__ == "__main__":
    # 用 stdio 作为传输方式，方便被本地 client 作为子进程拉起来
    mcp.run(transport="stdio")
