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
        text=True,
    )


def send_message(proc: subprocess.Popen, message: Dict[str, Any]) -> None:
    """按行发送一条 JSON-RPC 消息"""
    if proc.stdin is None:
        raise RuntimeError("server stdin is not available")

    line = json.dumps(message, ensure_ascii=False)
    print("CLIENT:", line)
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def read_message(proc: subprocess.Popen) -> Optional[Dict[str, Any]]:
    """读取并解析一行 JSON-RPC 响应"""
    if proc.stdout is None:
        raise RuntimeError("server stdout is not available")

    line = proc.stdout.readline()
    if not line:
        return None

    line = line.strip()
    if not line:
        return None

    try:
        message = json.loads(line)
    except json.JSONDecodeError:
        print("SERVER (raw):", line)
        return None

    print("SERVER:", message)
    return message


def main() -> None:
    server = run_server()

    try:
        # 1. initialize（补上 clientInfo）
        send_message(
            server,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {
                        "name": "simple-client",
                        "version": "0.1.0",
                    },
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
