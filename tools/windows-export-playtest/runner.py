import argparse
import asyncio
import base64
import json
import os
from pathlib import Path

from mcp import types
import windows_computer_use.server as WCU
from windows_computer_use import keymap

keymap.NAMED["game_r"] = 0x52


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(path: Path, event: str, **data):
    row = {"event": event, **data}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=True), flush=True)


async def save_shot(target: str, run_dir: Path, name: str, journal: Path):
    blocks = await WCU.screenshot(target=target, max_dim=1400)
    image = next(block for block in blocks if isinstance(block, types.ImageContent))
    path = run_dir / name
    path.write_bytes(base64.b64decode(image.data))
    append_log(journal, "screenshot", path=str(path))


async def run(args):
    config = load_json(Path(args.config))
    scenarios = load_json(Path(args.scenarios))
    scenario = scenarios[args.scenario]
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MCP_OUTPUT_DIR"] = str(run_dir)

    journal = run_dir / "actions.log"
    state_file = run_dir / "state.json"
    script = "\n".join(scenario["script"])
    pid = None
    state = {"phase": "starting", "scenario": args.scenario, "game_pid": None}
    write_json(state_file, state)
    append_log(journal, "run_start", scenario=args.scenario, game=config["game_exe"])

    try:
        launch = await WCU.process(
            "launch",
            exe=config["game_exe"],
            cwd=str(Path(config["game_exe"]).parent),
        )
        pid = launch.get("pid")
        state.update({"phase": "launched", "game_pid": pid})
        write_json(state_file, state)
        append_log(journal, "game_launch", result=launch)

        ready = await WCU.process(
            "wait_for_window",
            query=config["window_title"],
            timeout=float(config["window_ready_timeout_seconds"]),
            ready="input_idle",
        )
        append_log(journal, "window_ready", result=ready)
        focus = WCU.window("focus", query=config["window_title"])
        append_log(journal, "window_focus", result=focus)
        await save_shot(config["capture_target"], run_dir, "before.png", journal)

        state["phase"] = "armed"
        write_json(state_file, state)
        append_log(journal, "play_script", script=script)

        blocks = await WCU.play(
            script=script,
            target=config["capture_target"],
            fps=int(scenario.get("fps", 10)),
            montage_frames=int(scenario.get("montage_frames", 6)),
        )
        text = "\n".join(
            block.text for block in blocks if isinstance(block, types.TextContent)
        )
        append_log(journal, "play_result", text=text)

        montage = next(
            (block for block in blocks if isinstance(block, types.ImageContent)),
            None,
        )
        if montage:
            montage_path = run_dir / "montage.jpg"
            montage_path.write_bytes(base64.b64decode(montage.data))
            append_log(journal, "montage", path=str(montage_path))

        command_errors = [
            line.strip()
            for line in text.splitlines()
            if " ERROR " in f" {line} " or line.strip().startswith("ERROR")
        ]
        if command_errors:
            raise RuntimeError("PLAY_COMMAND_ERRORS: " + " | ".join(command_errors[:5]))
        if "stopped_by: end" not in text:
            raise RuntimeError("PLAY_DID_NOT_COMPLETE")

        await save_shot(config["capture_target"], run_dir, "after.png", journal)
        state["phase"] = "success"
        write_json(state_file, state)
        append_log(journal, "run_success", output_dir=str(run_dir))
        return 0

    except Exception as exc:
        state["phase"] = "error"
        state["error"] = str(exc)
        write_json(state_file, state)
        append_log(journal, "run_abort", reason=str(exc))
        raise
    finally:
        if pid:
            try:
                result = await WCU.process("kill", pid=pid)
                append_log(journal, "game_cleanup", result=result)
            except Exception as cleanup_error:
                append_log(journal, "cleanup_error", reason=str(cleanup_error))
        append_log(journal, "run_end")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--scenarios", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
