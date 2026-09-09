---
name: windows-export-playtest
description: Use when launching, controlling, screenshotting, recording, or black-box validating an exported Windows Godot build outside the editor, including held movement keys, restart input, focus/lock aborts, and release evidence.
---

# Windows Export Playtest

Use this skill for black-box evidence against the exported Windows `.exe`. It is tooling-only: do not change gameplay code, `project.godot`, input actions, or scenes to make automation easier.

## Default stack

Primary play-test tool: `sshh12/windows-computer-use-mcp`.

Known-good project-machine installation:
- repository: `C:\Users\Fixed\Tools\windows-computer-use-mcp`
- verified repository commit during setup: `8d367a8`
- venv: `.venv`
- current upstream package metadata allows MCP 2.x, but the checked code imports FastMCP 1.x; keep this venv on `mcp<2` until upstream fixes the constraint.

Use its upstream `process`, `window`, `screenshot`, and `play` capabilities rather than inventing a new SendInput/capture implementation. `play` already uses scan-code `SendInput`, supports `down`/`up`/`tap`, records a bounded MP4, and releases held keys/buttons in `finally`.

## Fast path

1. **Preflight.** Confirm the target `.exe` exists, the interactive Windows user session is active, and no previous play-test game/recorder process is running. OpenSSH runs in Session 0 and is not acceptable as GUI evidence.
2. **Tool health.** After installing/updating WCU or changing Python/MCP dependencies, run its own `tests\smoke_engine.py` once in the interactive session. Proceed only when all checks pass. Do not rerun this on every ordinary game test.
3. **Launch.** Start the exported `.exe` through WCU `process launch`, then `wait_for_window` and focus the exact game window. Capture an initial screenshot before sending input.
4. **Input.** Use WCU `play` for timed game input. Prefer named arrow keys (`left/right/up/down`) because they are layout-independent. If a letter key is required, resolve it to a tooling-only VK/scan-code alias; never alter the game's input map for automation.
5. **Guard.** Probe foreground/lock state between input phases. If the screen is locked or the game loses foreground focus, stop the test immediately and report `SCREEN_LOCKED` or `FOCUS_LOST:<window>`.
6. **Capture.** Record the physical monitor with WCU `play`. Godot/OpenGL windows may produce static frames through `PrintWindow`, so window capture is not proof unless visual change is independently confirmed.
7. **Cleanup.** The runner must kill only the game process it launched in `finally`. After every run, verify the task is idle and no game/recorder process remains.

## Required evidence

A successful run is not just "process exited 0". Preserve all of these from the same exported build:

- launch record: executable path and PID;
- initial screenshot from the real interactive desktop;
- action journal with timestamps and the exact input script;
- bounded MP4 showing the tested behavior;
- final screenshot/state check;
- cleanup record showing the launched game was terminated;
- one reproducible command that starts the same runner again.

For the current G1-style lifecycle proof, the minimum behavioral sequence is:

`launch .exe → screenshot → movement key down → key up → natural death → R → movement after restart → cleanup`

The log must distinguish an executed event from an intended event. An input command appearing in a script is not proof that the game reacted; confirm the result in screenshots/video or another external observation.

## Safety bounds

Every run is **bounded**. Default to a 10–15 second gameplay script. A task that is still running after ~30 seconds is abnormal: stop it, release input, terminate the launched game, and diagnose before retrying.

Write recordings outside the Godot repository, for example:
`C:\Users\Fixed\Videos\Necro-Export-Playtest\<timestamp>\`

Never use an unbounded Godot `--write-movie` process for routine black-box testing. A recorder must have a finite script/duration and must be owned by the runner that cleans it up.

Before declaring success, explicitly verify that no test-owned game, `ffmpeg`, or Movie Writer process remains. Do not infer cleanup from a task status alone.

## Known traps and chosen defaults

- **Session 0:** processes launched directly through Windows OpenSSH can run without a usable interactive window. Use an interactive-user task/launcher for the runner; use SSH only to trigger/check it.
- **Godot Movie Writer:** useful for engine-render capture, but it can run indefinitely and consume disk if ownership is lost. It is not the default play-test recorder.
- **PrintWindow/OpenGL:** WCU may capture a Godot window as identical/static frames even while the game is rendering. Prefer monitor capture for Godot runtime evidence.
- **Synthetic window messages:** `WM_KEYDOWN`, `PostMessage`, `SendKeys`, and similar approaches were not reliable evidence for Godot gameplay input. Use WCU scan-code `SendInput`.
- **Keyboard layout:** WCU's single-character lookup uses `VkKeyScanW`; Latin `A/D/R` can fail under a non-Latin active layout. Prefer named arrow keys, and use tooling-only VK aliases for required letter keys.
- **MCP Python SDK:** the verified WCU checkout used FastMCP 1.x APIs while declaring `mcp>=1.2.0`. If import fails after resolving to MCP 2.x, pin `mcp<2` in the WCU venv rather than editing project code.
- **Console encoding:** Windows task output may use a legacy code page. Journal JSON to UTF-8 first; treat console-print encoding failures as tooling failures, not game failures.

CursorTouch/Windows-MCP remains a useful general Windows UI MCP candidate for app/window/screenshot work, but WCU is the preferred export-playtest path because it already combines scan-code game input and bounded recording.

## Troubleshooting budget

Use a **bounded troubleshooting pass**:

1. Reproduce once with the smallest WCU/upstream test that isolates the failing layer.
2. Inspect upstream README/source/issues or research maintained alternatives before writing new automation.
3. Fix environment/configuration before code when the failure is outside the game.
4. After one failed custom-input/capture idea, stop extending it. Prefer a maintained tool or a short manual check.

Do not spend an implementation session building a Windows automation framework. The goal is to test the game, not to create another project.

## Current machine replay

The current Windows machine uses a manual-only interactive Scheduled Task named `Necro-Export-Playtest`. It is a launcher into the logged-in desktop session, not a background recorder or service.

From Windows:
```bat
schtasks /Run /TN "Necro-Export-Playtest"
```

From the VPS through the existing reverse SSH tunnel:
```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/id_ed25519_migration -p 2222 fixed@127.0.0.1 'schtasks /Run /TN "Necro-Export-Playtest"'
```

After triggering, check the task returns to `Ready`, then inspect the newest timestamped directory under:
`C:\Users\Fixed\Videos\Necro-Export-Playtest\`

If the task or runner is missing, recreate only the thin interactive launcher around WCU. Keep the game-control, capture, and bounded recording behavior in WCU rather than reimplementing them.
