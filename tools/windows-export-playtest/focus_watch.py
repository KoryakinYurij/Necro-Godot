import argparse
import json
import time
from pathlib import Path

from windows_computer_use import winfind

LOCK_PROCESSES = {"lockapp.exe", "logonui.exe"}


def classify(expected_title: str, expected_process: str):
    windows = winfind.list_windows()
    foreground = next((item for item in windows if item.get("foreground")), None)
    lock_windows = [
        item for item in windows
        if str(item.get("process", "")).lower() in LOCK_PROCESSES
    ]
    if foreground is None:
        if lock_windows:
            return "SCREEN_LOCKED"
        return "FOCUS_LOST:NONE"

    title = str(foreground.get("title", ""))
    process = str(foreground.get("process", "")).lower()
    if process in LOCK_PROCESSES or "lock screen" in title.lower():
        return "SCREEN_LOCKED"
    if expected_title.lower() not in title.lower() and expected_process.lower() not in process:
        return f"FOCUS_LOST:{title[:120] or process or 'UNKNOWN'}"
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-title", required=True)
    parser.add_argument("--expected-process", required=True)
    parser.add_argument("--poll-seconds", type=float, default=0.2)
    parser.add_argument("--stop-file", required=True)
    parser.add_argument("--reason-file", required=True)
    args = parser.parse_args()

    stop_file = Path(args.stop_file)
    reason_file = Path(args.reason_file)
    while not stop_file.exists():
        reason = classify(args.expected_title, args.expected_process)
        if reason:
            reason_file.write_text(
                json.dumps({"reason": reason}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(reason, flush=True)
            return 20
        time.sleep(max(0.05, args.poll_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
