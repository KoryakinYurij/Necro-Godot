import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import win32api
import win32con
import win32job
from windows_computer_use import winfind

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append_log(path, event, **data):
    row = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **data}
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=True), flush=True)


def create_kill_job():
    job = win32job.CreateJobObject(None, "")
    info = win32job.QueryInformationJobObject(
        job, win32job.JobObjectExtendedLimitInformation
    )
    info["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, info)
    return job


def assign_to_job(job, process):
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, process.pid)
    try:
        win32job.AssignProcessToJobObject(job, handle)
    finally:
        handle.Close()


def terminate_process(process, timeout=2.0):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=timeout)


def wait_for_armed(state_file, runner, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if runner.poll() is not None:
            return False
        if state_file.exists():
            state = load_json(state_file)
            if state.get("phase") == "armed":
                return True
        time.sleep(0.1)
    return False


def run_postcheck(wcu_python, tool_dir, state_file, run_dir, journal):
    result_file = run_dir / "postcheck.json"
    command = [
        wcu_python,
        str(tool_dir / "postcheck.py"),
        "--state-file", str(state_file),
        "--result-file", str(result_file),
    ]
    completed = subprocess.run(
        command,
        cwd=tool_dir,
        creationflags=CREATE_NO_WINDOW,
        timeout=8,
        check=False,
    )
    append_log(journal, "postcheck_exit", returncode=completed.returncode)
    return completed.returncode


def trigger_focus_loss(job, journal):
    process = subprocess.Popen(["notepad.exe"], creationflags=CREATE_NO_WINDOW)
    assign_to_job(job, process)
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        window = next(
            (
                item for item in winfind.list_windows()
                if str(item.get("process", "")).lower() == "notepad.exe"
            ),
            None,
        )
        if window:
            focused = winfind.foreground(window["hwnd"])
            append_log(journal, "focus_loss_triggered", focused=focused, title=window.get("title", ""))
            return process
        time.sleep(0.1)
    append_log(journal, "focus_loss_trigger_failed")
    return process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--scenario")
    args = parser.parse_args()

    tool_dir = Path(__file__).resolve().parent
    config = load_json(args.config)
    scenarios_path = tool_dir / "scenarios.json"
    scenarios = load_json(scenarios_path)
    scenario_name = args.scenario or config.get("scenario", "g1-lifecycle")
    scenario = scenarios[scenario_name]
    deadline_seconds = float(scenario["deadline_seconds"])

    run_dir = Path(config["output_root"]) / f"{time.strftime('%Y%m%d-%H%M%S')}-{scenario_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    journal = run_dir / "actions.log"
    state_file = run_dir / "state.json"
    stop_file = run_dir / "focus-watch.stop"
    reason_file = run_dir / "focus-abort.json"
    (tool_dir / "last-run.json").write_text(
        json.dumps({"run_dir": str(run_dir), "scenario": scenario_name}, indent=2),
        encoding="utf-8",
    )
    append_log(journal, "launcher_start", scenario=scenario_name, deadline_seconds=deadline_seconds)

    wcu_python = config["wcu_python"]
    runner_command = [
        wcu_python,
        str(tool_dir / "runner.py"),
        "--config", str(Path(args.config).resolve()),
        "--scenarios", str(scenarios_path),
        "--scenario", scenario_name,
        "--run-dir", str(run_dir),
    ]
    job = create_kill_job()
    runner = None
    watcher = None
    auxiliary = []
    started = time.monotonic()

    try:
        runner = subprocess.Popen(
            runner_command,
            cwd=tool_dir,
            creationflags=CREATE_NO_WINDOW,
        )
        assign_to_job(job, runner)
        append_log(journal, "runner_started", pid=runner.pid)

        armed_timeout = min(
            deadline_seconds,
            float(config["window_ready_timeout_seconds"]) + 4.0,
        )
        if not wait_for_armed(state_file, runner, armed_timeout):
            raise RuntimeError("RUNNER_DID_NOT_ARM")
        armed_at = time.monotonic()
        append_log(journal, "runner_armed", elapsed=round(armed_at - started, 3))

        watcher_command = [
            wcu_python,
            str(tool_dir / "focus_watch.py"),
            "--expected-title", config["window_title"],
            "--expected-process", config["game_process_name"],
            "--poll-seconds", str(config["focus_poll_seconds"]),
            "--stop-file", str(stop_file),
            "--reason-file", str(reason_file),
        ]
        watcher = subprocess.Popen(
            watcher_command,
            cwd=tool_dir,
            creationflags=CREATE_NO_WINDOW,
        )
        assign_to_job(job, watcher)
        append_log(journal, "focus_watch_started", pid=watcher.pid)

        focus_loss_after = scenario.get("focus_loss_after_seconds")
        focus_triggered = False
        safety_reason = None

        while runner.poll() is None:
            elapsed = time.monotonic() - started
            if elapsed > deadline_seconds:
                safety_reason = "DEADLINE_EXCEEDED"
                break
            if watcher.poll() is not None and watcher.returncode != 0:
                if reason_file.exists():
                    safety_reason = load_json(reason_file).get("reason", "FOCUS_WATCH_ABORT")
                else:
                    safety_reason = "FOCUS_WATCH_ABORT"
                break

            if (
                focus_loss_after is not None
                and not focus_triggered
                and time.monotonic() - armed_at >= float(focus_loss_after)
            ):
                auxiliary.append(trigger_focus_loss(job, journal))
                focus_triggered = True
            time.sleep(0.1)

        if safety_reason:
            append_log(journal, "safety_abort", reason=safety_reason)
            terminate_process(runner)
            stop_file.touch()
            terminate_process(watcher)
            postcheck_rc = run_postcheck(
                wcu_python, tool_dir, state_file, run_dir, journal
            )
            append_log(
                journal,
                "launcher_abort_complete",
                reason=safety_reason,
                postcheck_returncode=postcheck_rc,
            )
            return 124 if safety_reason == "DEADLINE_EXCEEDED" else 125

        runner_rc = runner.returncode
        stop_file.touch()
        if watcher.poll() is None:
            watcher.wait(timeout=3)
        postcheck_rc = run_postcheck(
            wcu_python, tool_dir, state_file, run_dir, journal
        )

        if runner_rc == 0 and postcheck_rc == 0:
            append_log(journal, "launcher_success")
            return 0
        append_log(
            journal,
            "launcher_failure",
            runner_returncode=runner_rc,
            postcheck_returncode=postcheck_rc,
        )
        return runner_rc or postcheck_rc or 1

    except Exception as exc:
        append_log(journal, "launcher_exception", reason=str(exc))
        terminate_process(runner)
        stop_file.touch()
        terminate_process(watcher)
        if state_file.exists():
            try:
                run_postcheck(wcu_python, tool_dir, state_file, run_dir, journal)
            except Exception as postcheck_error:
                append_log(journal, "postcheck_exception", reason=str(postcheck_error))
        return 2
    finally:
        for process in auxiliary:
            terminate_process(process)
        terminate_process(watcher)
        terminate_process(runner)
        job.Close()
        append_log(journal, "launcher_end")


if __name__ == "__main__":
    raise SystemExit(main())
