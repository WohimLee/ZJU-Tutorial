# server_ws_fastapi.py
import json
import os
from typing import Dict, Any

import requests
from tavily import TavilyClient

from fastapi import FastAPI
from starlette.responses import PlainTextResponse
import uvicorn

from mcp.server.fastmcp import FastMCP
from mcp.server.websocket import websocket_server

from dotenv import load_dotenv
load_dotenv("/Users/azen/Desktop/llm/ZJU-Tutorial/.env")

# ========================================
# 1. 创建 FastMCP 实例 & 工具
# ========================================

mcp_server = FastMCP("WeatherAndTavilyServer")


@mcp_server.tool()
def get_weather(city: str) -> str:
    """
    查询指定城市天气。
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
        for k in key_selection:
            if data.get(k):
                ret[k] = {}
                for field in key_selection[k]:
                    value = data[k][0].get(field)
                    if field == "weatherDesc" and isinstance(value, list):
                        value = value[0].get("value")
                    ret[k][field] = value

        return json.dumps(ret, ensure_ascii=False)

    except Exception as e:
        return f"Error fetching weather: {e!r}"


@mcp_server.tool()
def search_info_by_tavily(query: str) -> str:
    """
    Tavily 搜索工具。
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "TAVILY_API_KEY 未设置"

    client = TavilyClient(api_key)
    try:
        data = client.search(query)
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return f"Tavily 调用失败: {e!r}"


# ========================================
# 2. MCP WebSocket ASGI 应用
# ========================================

async def mcp_asgi_app(scope, receive, send):
    """
    低层 ASGI 写法：
    - 如果不是 websocket，就返回 400
    - 如果是 websocket，就交给 websocket_server 来处理 MCP 协议
    """
    if scope["type"] != "websocket":
        resp = PlainTextResponse(
            "This is an MCP WebSocket endpoint. Please connect via WebSocket.",
            status_code=400,
        )
        await resp(scope, receive, send)
        return

    # 交给 MCP 的 websocket_server 做握手 + JSON-RPC
    async with websocket_server(scope, receive, send) as (read_stream, write_stream):
        await mcp_server._mcp_server.run(
            read_stream,
            write_stream,
            mcp_server._mcp_server.create_initialization_options(),
        )


# ========================================
# 3. FastAPI 主应用：把 /mcp 挂载为 MCP WebSocket 端点
# ========================================

app = FastAPI()
app.mount("/mcp", mcp_asgi_app)


if __name__ == "__main__":
    # WebSocket 地址：ws://127.0.0.1:8000/mcp
    uvicorn.run(app, host="127.0.0.1", port=8000)
