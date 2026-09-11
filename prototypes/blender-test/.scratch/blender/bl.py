"""Run a local .py file inside the running Blender via the blender-mcp addon socket.

Usage:  python .scratch/blender/bl.py .scratch/blender/01_inspect.py

The addon exposes execute_code(code) on 127.0.0.1:9876 (JSON per message).
The code runs on Blender's main thread, so keep it context-free: no bpy.ops
that need a specific area/region unless wrapped in temp_override.
"""

import json
import socket
import sys
import time
from pathlib import Path

HOST, PORT = "127.0.0.1", 9876


def call(cmd, timeout=600.0, **params):
    deadline = time.time() + timeout
    sock = socket.create_connection((HOST, PORT), timeout=timeout)
    try:
        payload = json.dumps({"type": cmd, "params": params}).encode("utf-8")
        sock.sendall(payload)
        buf = b""
        while time.time() < deadline:
            data = sock.recv(1 << 20)
            if not data:
                break
            buf += data
            try:
                return json.loads(buf.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        return {"status": "error", "message": f"no parseable response ({len(buf)} bytes)"}
    finally:
        sock.close()


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python bl.py <script.py>", file=sys.stderr)
        return 2

    code = Path(sys.argv[1]).read_text(encoding="utf-8")
    response = call("execute_code", code=code)

    if response.get("status") != "success":
        print("STATUS: error")
        print(json.dumps(response, ensure_ascii=False)[:4000])
        return 1

    stdout_text = response.get("result", {}).get("result", "")
    if stdout_text:
        print(stdout_text.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
