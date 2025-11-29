import asyncio
import json
from typing import Any, Dict

import websockets
from websockets.server import WebSocketServerProtocol

HOST = "127.0.0.1"
PORT = 8765


def handle_request(msg: Dict[str, Any]) -> Dict[str, Any]:
    """根据 method 处理 JSON-RPC 请求，返回响应 dict"""
    jsonrpc = msg.get("jsonrpc", "2.0")
    req_id = msg.get("id")

    method = msg.get("method")
    params = msg.get("params", {})

    try:
        if method == "initialize":
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "protocolVersion": params.get("protocolVersion", "2024-05-16"),
                    "serverInfo": {
                        "name": "websocket-mcp-demo",
                        "version": "0.1.0",
                    },
                    "capabilities": {
                        "tools": {},
                    },
                },
            }

        if method == "tools/list":
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "hello",
                            "description": "Say hello to someone.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                },
                                "required": ["name"],
                            },
                        }
                    ]
                },
            }

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})

            if name != "hello":
                raise ValueError(f"Unknown tool: {name}")

            who = arguments.get("name", "world")
            result_text = f"Hello, {who}! This is WebSocket MCP demo."

            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text,
                        }
                    ]
                },
            }

        raise ValueError(f"Unknown method: {method}")

    except Exception as e:
        return {
            "jsonrpc": jsonrpc,
            "id": req_id,
            "error": {
                "code": -32602,
                "message": "Invalid request",
                "data": str(e),
            },
        }


async def handler(websocket: WebSocketServerProtocol) -> None:
    print("[SERVER] client connected")
    try:
        async for message in websocket:
            print("[SERVER] recv:", message)
            try:
                msg = json.loads(message)
            except json.JSONDecodeError as e:
                print("[SERVER] JSON decode error:", e)
                continue

            resp = handle_request(msg)
            resp_text = json.dumps(resp, ensure_ascii=False)
            print("[SERVER] send:", resp_text)
            await websocket.send(resp_text)
    finally:
        print("[SERVER] client disconnected")


async def main() -> None:
    async with websockets.serve(handler, HOST, PORT):
        print(f"[SERVER] Listening on ws://{HOST}:{PORT}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
