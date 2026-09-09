import argparse
import ctypes
import json
import time
from pathlib import Path

from windows_computer_use import input as winput
from windows_computer_use import keymap
from windows_computer_use import process as wprocess

keymap.NAMED["game_r"] = 0x52
KEYS = ["left", "right", "up", "down", "game_r"]

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
kernel32.OpenProcess.restype = ctypes.c_void_p
kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def process_alive(pid):
    if not pid:
        return False
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not handle:
        return False
    kernel32.CloseHandle(handle)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--result-file", required=True)
    args = parser.parse_args()

    state_path = Path(args.state_file)
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    pid = state.get("game_pid")

    release_errors = {}
    for key in KEYS:
        try:
            winput.key_up(key)
        except Exception as exc:
            release_errors[key] = str(exc)
    time.sleep(0.1)

    key_down = {
        key: bool(user32.GetAsyncKeyState(keymap.resolve_vk(key)) & 0x8000)
        for key in KEYS
    }

    kill_result = None
    if process_alive(pid):
        kill_result = wprocess.kill(int(pid))
        time.sleep(0.2)
    game_alive = process_alive(pid)

    result = {
        "keys_released": not any(key_down.values()) and not release_errors,
        "key_down": key_down,
        "release_errors": release_errors,
        "game_pid": pid,
        "game_alive": game_alive,
        "kill_result": kill_result,
    }
    Path(args.result_file).write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=True), flush=True)
    return 0 if result["keys_released"] and not game_alive else 2


if __name__ == "__main__":
    raise SystemExit(main())
