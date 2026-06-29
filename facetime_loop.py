import subprocess
import time
import sys
import random
import argparse
import json
import os
import signal
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

CONFIG_FILE = "config.json"
_cfg = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        _cfg = json.load(f)

def cfg(key, default):
    return _cfg.get(key, default)

parser = argparse.ArgumentParser(description="FaceTime Loop — agentic calling agent")
parser.add_argument("--number", "-n", action="append", help="Number to call (can be used multiple times)")
parser.add_argument("--delay", "-d", type=int, help="Seconds between calls")
parser.add_argument("--max-attempts", "-m", type=int, help="Max attempts per number")
parser.add_argument("--start-time", "-s", help="Start time HH:MM")
parser.add_argument("--stop-time", help="Stop time HH:MM")
parser.add_argument("--round-robin", action="store_true", help="Enable round-robin mode")
parser.add_argument("--repeat-daily", action="store_true", help="Repeat session daily")
parser.add_argument("--max-daily", type=int, help="Max total calls per session")
args = parser.parse_args()

LOG_FILE          = cfg("log_file", "call_log.txt")
START_TIME        = cfg("start_time", None)
STOP_TIME         = cfg("stop_time", None)
BLACKOUT_START    = cfg("blackout_start", 22)
BLACKOUT_END      = cfg("blackout_end", 8)
BLACKOUT_ENABLED  = cfg("blackout_enabled", False)
ALLOWED_DAYS      = cfg("allowed_days", None)
NUMBERS           = cfg("numbers", {"+919324718705": 1})
NUMBERS_FILE      = cfg("numbers_file", None)
DELAY             = cfg("delay", 20)
DELAY_RANDOM      = cfg("delay_random", True)
MAX_ATTEMPTS      = cfg("max_attempts", 10)
NUMBER_COOLDOWN   = cfg("number_cooldown", 30)
MAX_DAILY_CALLS   = cfg("max_daily_calls", 50)
SKIP_AFTER_FAILURES = cfg("skip_after_failures", 3)
ROUND_ROBIN       = cfg("round_robin", False)
REPEAT_DAILY      = cfg("repeat_daily", False)
EMAIL_ENABLED     = cfg("email_enabled", False)
EMAIL_SENDER      = cfg("email_sender", "")       # your Gmail address
EMAIL_PASSWORD    = cfg("email_password", "")     # Gmail app password
EMAIL_RECIPIENT   = cfg("email_recipient", "")    # where to send the summary

# CLI args override config values when provided
if args.number:
    NUMBERS = {n: 1 for n in args.number}
if args.delay:
    DELAY = args.delay
if args.max_attempts:
    MAX_ATTEMPTS = args.max_attempts
if args.start_time:
    START_TIME = args.start_time
if args.stop_time:
    STOP_TIME = args.stop_time
if args.round_robin:
    ROUND_ROBIN = True
if args.repeat_daily:
    REPEAT_DAILY = True
if args.max_daily:
    MAX_DAILY_CALLS = args.max_daily

def generate_html_report(total_calls, duration_secs):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = ""
    try:
        with open(LOG_FILE) as f:
            for line in f:
                rows += f"<tr><td>{line.strip()}</td></tr>\n"
    except FileNotFoundError:
        rows = "<tr><td>No log entries found.</td></tr>"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>FaceTime Loop Report</title>
<style>body{{font-family:sans-serif;padding:20px}}table{{width:100%;border-collapse:collapse}}
td{{border:1px solid #ccc;padding:6px 10px;font-size:13px}}h1{{color:#333}}</style>
</head><body>
<h1>FaceTime Loop — Session Report</h1>
<p><b>Date:</b> {date_str} | <b>Total calls:</b> {total_calls} | <b>Duration:</b> {int(duration_secs//60)}m {int(duration_secs%60)}s</p>
<p><b>Numbers:</b> {', '.join(NUMBERS.keys())}</p>
<h2>Log</h2><table>{rows}</table>
</body></html>"""
    report_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_file, "w") as f:
        f.write(html)
    log(f"HTML report saved: {report_file}")

def send_email_summary(total_calls, duration_secs):
    if not EMAIL_ENABLED or not EMAIL_SENDER:
        return
    try:
        body = (f"FaceTime Loop session complete.\n\n"
                f"Total calls made: {total_calls}\n"
                f"Duration: {int(duration_secs // 60)}m {int(duration_secs % 60)}s\n"
                f"Numbers called: {', '.join(NUMBERS.keys())}\n")
        msg = MIMEText(body)
        msg["Subject"] = f"FaceTime Loop — {total_calls} calls made"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECIPIENT
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        log(f"Email summary sent to {EMAIL_RECIPIENT}.")
    except Exception as e:
        log(f"Email failed: {e}")

def play_sound():
    subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"], capture_output=True)

def notify(title, message):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "{title}"'
    ], capture_output=True)

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def in_blackout():
    if not BLACKOUT_ENABLED:
        return False
    hour = datetime.now().hour
    if BLACKOUT_START > BLACKOUT_END:  # spans midnight
        return hour >= BLACKOUT_START or hour < BLACKOUT_END
    return BLACKOUT_START <= hour < BLACKOUT_END

def wait_through_blackout():
    while in_blackout():
        log(f"Blackout hours ({BLACKOUT_START}:00–{BLACKOUT_END}:00). Waiting 60s...")
        time.sleep(60)

def past_stop_time():
    if not STOP_TIME:
        return False
    now = datetime.now()
    stop = datetime.strptime(datetime.now().strftime("%Y-%m-%d") + " " + STOP_TIME, "%Y-%m-%d %H:%M")
    return now >= stop

def wait_until(start_time_str):
    target = datetime.strptime(
        datetime.now().strftime("%Y-%m-%d") + " " + start_time_str,
        "%Y-%m-%d %H:%M"
    )
    now = datetime.now()
    if target <= now:
        log(f"Scheduled time {start_time_str} already passed — starting now.")
        return
    wait_secs = (target - now).total_seconds()
    log(f"Waiting until {start_time_str} ({int(wait_secs)}s from now)...")
    time.sleep(wait_secs)

if NUMBERS_FILE:
    try:
        with open(NUMBERS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(":")
                num = parts[0].strip()
                priority = int(parts[1].strip()) if len(parts) > 1 else 1
                NUMBERS[num] = priority
        log(f"Loaded {len(NUMBERS)} number(s) from {NUMBERS_FILE}.")
    except FileNotFoundError:
        log(f"Numbers file '{NUMBERS_FILE}' not found. Using hardcoded NUMBERS.")

if ALLOWED_DAYS:
    today = datetime.now().strftime("%A")
    if today not in ALLOWED_DAYS:
        log(f"Today is {today}, not in allowed days {ALLOWED_DAYS}. Exiting.")
        sys.exit(0)

sorted_numbers = sorted(NUMBERS.items(), key=lambda x: x[1], reverse=True)
call_list = [num for num, _ in sorted_numbers]

session_start_time = None
_paused = False

def toggle_pause(signum, frame):
    global _paused
    _paused = not _paused
    state = "PAUSED (send SIGUSR1 again to resume)" if _paused else "RESUMED"
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {state}")

signal.signal(signal.SIGUSR1, toggle_pause)
print(f"PID {os.getpid()} — send 'kill -SIGUSR1 {os.getpid()}' to pause/resume")

def live_countdown(seconds, label="Next call in"):
    for remaining in range(int(seconds), 0, -1):
        while _paused:
            print(f"\r  [PAUSED] Press kill -SIGUSR1 {os.getpid()} to resume   ", end="", flush=True)
            time.sleep(1)
        elapsed = int(time.time() - session_start_time) if session_start_time else 0
        print(f"\r  {label}: {remaining:3}s | session elapsed: {elapsed}s   ", end="", flush=True)
        time.sleep(1)
    print()

def run_call(NUMBER, attempt, total_calls):
    play_sound()
    notify("FaceTime Loop", f"Calling {NUMBER} (attempt {attempt})")
    subprocess.run(["open", f"facetime://{NUMBER}"])
    wait = random.uniform(DELAY, DELAY * 1.5) if DELAY_RANDOM else DELAY
    log(f"[{NUMBER}] Call {attempt} (total: {total_calls}). Next in {int(wait)}s...")
    live_countdown(wait)

def run_session():
    global session_start_time
    session_start_time = time.time()
    total_calls = 0
    log(f"Session started. Calling {len(call_list)} number(s) on FaceTime (by priority).")
    if MAX_ATTEMPTS:
        log(f"Will stop after {MAX_ATTEMPTS} attempts per number.")
    if MAX_DAILY_CALLS:
        log(f"Daily cap: {MAX_DAILY_CALLS} total calls.")
    try:
        if ROUND_ROBIN:
            round_attempt = {n: 0 for n in call_list}
            active = list(call_list)
            while active:
                for NUMBER in list(active):
                    if MAX_DAILY_CALLS and total_calls >= MAX_DAILY_CALLS:
                        log(f"Daily cap reached. Stopping."); raise StopIteration
                    if past_stop_time():
                        log(f"Stop time reached. Stopping."); raise StopIteration
                    wait_through_blackout()
                    round_attempt[NUMBER] += 1
                    total_calls += 1
                    run_call(NUMBER, round_attempt[NUMBER], total_calls)
                    if MAX_ATTEMPTS and round_attempt[NUMBER] >= MAX_ATTEMPTS:
                        log(f"Max attempts reached for {NUMBER}. Removing from rotation.")
                        active.remove(NUMBER)
        else:
            for i, NUMBER in enumerate(call_list):
                if MAX_DAILY_CALLS and total_calls >= MAX_DAILY_CALLS:
                    log(f"Daily cap of {MAX_DAILY_CALLS} calls reached. Stopping.")
                    break
                if i > 0 and NUMBER_COOLDOWN:
                    log(f"Cooldown: waiting {NUMBER_COOLDOWN}s before next number...")
                    time.sleep(NUMBER_COOLDOWN)
                attempt = 0
                consecutive_failures = 0
                log(f"Starting calls to {NUMBER} (priority {NUMBERS[NUMBER]})")
                while True:
                    if MAX_ATTEMPTS and attempt >= MAX_ATTEMPTS:
                        log(f"Reached {MAX_ATTEMPTS} attempts for {NUMBER}. Moving on.")
                        break
                    if SKIP_AFTER_FAILURES and consecutive_failures >= SKIP_AFTER_FAILURES:
                        log(f"Skipping {NUMBER} after {consecutive_failures} consecutive unanswered calls.")
                        break
                    if MAX_DAILY_CALLS and total_calls >= MAX_DAILY_CALLS:
                        log(f"Daily cap of {MAX_DAILY_CALLS} calls reached. Stopping.")
                        raise StopIteration
                    if past_stop_time():
                        log(f"Stop time {STOP_TIME} reached. Stopping.")
                        raise StopIteration
                    wait_through_blackout()
                    attempt += 1
                    total_calls += 1
                    consecutive_failures += 1
                    run_call(NUMBER, attempt, total_calls)
    except StopIteration:
        pass
    duration = time.time() - session_start_time
    log(f"Session ended. Total calls made: {total_calls} in {int(duration)}s.")
    generate_html_report(total_calls, duration)
    send_email_summary(total_calls, duration)
    return total_calls

try:
    while True:
        if START_TIME:
            wait_until(START_TIME)
        run_session()
        if not REPEAT_DAILY:
            break
        log("Waiting 24 hours before next session...")
        time.sleep(86400)
except KeyboardInterrupt:
    log("Stopped by user.")
