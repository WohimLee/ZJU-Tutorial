import json
import socket
import sys
import threading
from typing import Any, Dict

HOST = "127.0.0.1"
PORT = 8765


# ======== JSON-RPC 工具实现（模拟 MCP server） ========

def handle_request(msg: Dict[str, Any]) -> Dict[str, Any]:
    """根据 method 处理 JSON-RPC 请求，返回响应 dict"""
    jsonrpc = msg.get("jsonrpc", "2.0")
    req_id = msg.get("id")

    method = msg.get("method")
    params = msg.get("params", {})

    try:
        if method == "initialize":
            # 简化版初始化：直接返回 ok
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "protocolVersion": params.get("protocolVersion", "2024-05-16"),
                    "serverInfo": {
                        "name": "tcp-mcp-demo",
                        "version": "0.1.0",
                    },
                    "capabilities": {
                        "tools": {},
                    },
                },
            }

        if method == "tools/list":
            # 返回一个叫 hello 的“工具”
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
            result_text = f"Hello, {who}! This is TCP MCP demo."

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

        # 未知 method
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


# ======== TCP Server 部分 ========

def handle_client(conn: socket.socket, addr) -> None:
    print(f"[SERVER] Client connected from {addr}")
    f = conn.makefile(mode="r+", encoding="utf-8", buffering=1)

    try:
        for line in f:
            line = line.strip()
            if not line:
                continue

            print("[SERVER] recv:", line)
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                print("[SERVER] JSON decode error:", e)
                continue

            resp = handle_request(msg)
            resp_line = json.dumps(resp, ensure_ascii=False)
            print("[SERVER] send:", resp_line)
            f.write(resp_line + "\n")
            f.flush()
    finally:
        print(f"[SERVER] Client {addr} disconnected")
        f.close()
        conn.close()


def run_server() -> None:
    """运行 TCP 版本的“MCP server”"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[SERVER] Listening on {HOST}:{PORT} ...")

        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


# ======== TCP Client 部分（模拟 MCP client） ========

def send_and_recv(f, msg: Dict[str, Any]) -> None:
    line = json.dumps(msg, ensure_ascii=False)
    print("[CLIENT] send:", line)
    f.write(line + "\n")
    f.flush()

    resp = f.readline()
    if not resp:
        print("[CLIENT] no response")
        return

    resp = resp.strip()
    print("[CLIENT] recv:", resp)


def run_client() -> None:
    """连接 TCP server，执行 initialize -> tools/list -> tools/call"""
    with socket.create_connection((HOST, PORT)) as s:
        f = s.makefile(mode="r+", encoding="utf-8", buffering=1)

        # 1. initialize
        send_and_recv(
            f,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-05-16",
                    "clientInfo": {
                        "name": "tcp-client",
                        "version": "0.1.0",
                    },
                    "capabilities": {},
                },
            },
        )

        # 2. list tools
        send_and_recv(
            f,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )

        # 3. call tool
        send_and_recv(
            f,
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


# ======== 入口 ========

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "client"
    if mode == "server":
        run_server()
    elif mode == "client":
        run_client()
    else:
        print("Usage:")
        print("  python simple_mcp_tcp_demo.py server")
        print("  python simple_mcp_tcp_demo.py client")
