import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def run_server() -> subprocess.Popen:
    """启动 simple_mcp 的 server（使用与当前 Python 一致的解释器）"""
    server_script = Path(__file__).with_name("server.py")
    return subprocess.Popen(
        [sys.executable, str(server_script)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
    )


def send_message(proc: subprocess.Popen, message: Dict[str, Any]) -> None:
    """按 MCP STDIO 规范发送一条 JSON-RPC 消息（带 Content-Length 头）"""
    if proc.stdin is None:
        raise RuntimeError("server stdin is not available")

    body_bytes = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("ascii")

    print("CLIENT:", message)
    proc.stdin.write(header + body_bytes)
    proc.stdin.flush()


def read_message(proc: subprocess.Popen) -> Optional[Dict[str, Any]]:
    """从 STDIO 读取一条 JSON-RPC 消息"""
    if proc.stdout is None:
        raise RuntimeError("server stdout is not available")

    content_length: Optional[int] = None

    # 读取 header
    while True:
        line = proc.stdout.readline()
        if not line:
            return None

        if line in (b"\r\n", b"\n"):
            break

        header_line = line.decode("ascii", errors="ignore").strip()
        if header_line.lower().startswith("content-length:"):
            _, value = header_line.split(":", 1)
            content_length = int(value.strip())

    if content_length is None:
        return None

    # 读取 body
    body = proc.stdout.read(content_length)
    if not body:
        return None

    message = json.loads(body.decode("utf-8"))
    print("SERVER:", message)
    return message


def main() -> None:
    server = run_server()

    try:
        # 1. initialize
        send_message(
            server,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                },
            },
        )
        read_message(server)

        # 2. list tools
        send_message(
            server,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )
        read_message(server)

        # 3. call tool
        send_message(
            server,
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
        read_message(server)
    finally:
        if server.stdin and not server.stdin.closed:
            server.stdin.close()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
