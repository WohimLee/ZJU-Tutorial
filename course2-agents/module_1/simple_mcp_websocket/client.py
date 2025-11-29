import asyncio
import json

import websockets

HOST = "127.0.0.1"
PORT = 8765
WS_URL = f"ws://{HOST}:{PORT}"


async def send_and_recv(ws, msg):
    text = json.dumps(msg, ensure_ascii=False)
    print("[CLIENT] send:", text)
    await ws.send(text)

    resp = await ws.recv()
    print("[CLIENT] recv:", resp)


async def main():
    async with websockets.connect(WS_URL) as ws:
        # 1. initialize
        await send_and_recv(
            ws,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-05-16",
                    "clientInfo": {
                        "name": "ws-client",
                        "version": "0.1.0",
                    },
                    "capabilities": {},
                },
            },
        )

        # 2. list tools
        await send_and_recv(
            ws,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )

        # 3. call tool
        await send_and_recv(
            ws,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "hello",
                    "arguments": {"name": "Alice"},
                },
            },
        )


if __name__ == "__main__":
    asyncio.run(main())
