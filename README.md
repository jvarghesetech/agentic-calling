# agentic-calling

An agentic FaceTime calling loop for macOS. Automatically calls one or more numbers on repeat with full scheduling, logging, and reporting support.

## Usage

```bash
python3 facetime_loop.py
```

Or override settings via CLI:

```bash
python3 facetime_loop.py --number +1234567890 --delay 30 --max-attempts 5
python3 facetime_loop.py -n +1111111111 -n +2222222222 --round-robin
python3 facetime_loop.py --start-time 09:00 --stop-time 22:00 --repeat-daily
```

## Configuration

All settings can be set in `config.json` (recommended) or directly in `facetime_loop.py`.

### `config.json` reference

```json
{
  "numbers": {"+919324718705": 1},
  "delay": 20,
  "delay_random": true,
  "max_attempts": 10,
  "number_cooldown": 30,
  "max_daily_calls": 50,
  "skip_after_failures": 3,
  "round_robin": false,
  "repeat_daily": false,
  "start_time": null,
  "stop_time": null,
  "blackout_enabled": false,
  "blackout_start": 22,
  "blackout_end": 8,
  "allowed_days": null,
  "numbers_file": null,
  "log_file": "call_log.txt",
  "email_enabled": false,
  "email_sender": "",
  "email_password": "",
  "email_recipient": "",
  "retry_quick_delay": 5,
  "retry_quick_attempts": 2
}
```

## Features

| # | Feature | How to use |
|---|---------|-----------|
| 1 | **Stop after N attempts** | `max_attempts` in config or `--max-attempts` |
| 2 | **Multiple numbers** | Add to `numbers` dict in config or `-n` flag |
| 3 | **Call history log** | Automatically saved to `call_log.txt` |
| 4 | **Schedule start time** | `start_time: "14:30"` or `--start-time 14:30` |
| 5 | **Randomized delay** | `delay_random: true` (randomizes between `delay` and `delay * 1.5`) |
| 6 | **Cooldown between numbers** | `number_cooldown: 30` (seconds) |
| 7 | **Max total calls per day** | `max_daily_calls: 50` or `--max-daily 50` |
| 8 | **Stop time** | `stop_time: "22:00"` or `--stop-time 22:00` |
| 9 | **Blackout hours** | `blackout_enabled: true`, `blackout_start: 22`, `blackout_end: 8` |
| 10 | **Days of week** | `allowed_days: ["Monday","Tuesday","Wednesday","Thursday","Friday"]` |
| 11 | **Mac notification** | Automatic — pops a system notification on each call |
| 12 | **Sound alert** | Automatic — plays Ping sound on each call |
| 13 | **Call priority order** | Set higher numbers in `numbers` dict: `{"+1111": 2, "+2222": 1}` |
| 14 | **Load numbers from file** | `numbers_file: "numbers.txt"` — one number per line, optional `:priority` |
| 15 | **Skip after X failures** | `skip_after_failures: 3` |
| 16 | **Round-robin mode** | `round_robin: true` or `--round-robin` |
| 17 | **Repeat daily** | `repeat_daily: true` or `--repeat-daily` |
| 18 | **Live status display** | Automatic — shows countdown + elapsed time in terminal |
| 19 | **Pause / Resume** | Send `kill -SIGUSR1 <PID>` to toggle pause (PID shown on startup) |
| 20 | **CLI arguments** | Run with `--help` to see all flags |
| 21 | **Config file** | Edit `config.json` — no code changes needed |
| 22 | **Email summary** | Set `email_enabled: true` with Gmail sender/password/recipient |
| 23 | **HTML report** | Automatic — generates `report_YYYYMMDD_HHMMSS.html` after each session |
| 24 | **Quick retry on no answer** | `retry_quick_attempts: 2`, `retry_quick_delay: 5` |
| 25 | **Statistics dashboard** | Automatic — printed to terminal at end of each session |

## Numbers file format

```
+919324718705
+14155552671:2
+14155552672:1
```

Lines starting with `#` are ignored. The `:priority` suffix is optional (default 1).

## Email setup

Uses Gmail SMTP with an [App Password](https://support.google.com/accounts/answer/185833).

```json
{
  "email_enabled": true,
  "email_sender": "you@gmail.com",
  "email_password": "your-app-password",
  "email_recipient": "you@gmail.com"
}
```

## Requirements

- macOS (uses `open facetime://`, `osascript`, `afplay`)
- Python 3.7+
- No external dependencies
