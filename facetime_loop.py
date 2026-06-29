import subprocess
import time
import sys
import random
from datetime import datetime

LOG_FILE = "call_log.txt"

# Schedule: set to "HH:MM" (24hr) to delay until that time, or None to start immediately
START_TIME = None   # e.g. "14:30" to start at 2:30 PM
STOP_TIME  = None   # e.g. "22:00" to stop at 10:00 PM
BLACKOUT_START = 22  # hour (24hr) to start blackout, e.g. 22 = 10 PM
BLACKOUT_END   = 8   # hour (24hr) to end blackout, e.g. 8 = 8 AM
BLACKOUT_ENABLED = False
ALLOWED_DAYS = None  # e.g. ["Monday","Tuesday","Wednesday","Thursday","Friday"] for weekdays only; None = all days

# Numbers with priority — higher number = called first. Same priority = original order.
NUMBERS = {"+919324718705": 1}  # format: {"number": priority}
NUMBERS_FILE = None  # e.g. "numbers.txt" — one number per line, optional ":priority" suffix
DELAY = 20          # base seconds between calls
DELAY_RANDOM = True # if True, randomizes delay between DELAY and DELAY*1.5
MAX_ATTEMPTS = 10   # set to None for unlimited
NUMBER_COOLDOWN = 30  # seconds to wait before moving to next number
MAX_DAILY_CALLS = 50  # hard cap on total calls per session, set to None for unlimited
SKIP_AFTER_FAILURES = 3  # skip a number after this many consecutive unanswered calls; None = never skip
ROUND_ROBIN = False      # if True, rotate through all numbers on each attempt instead of exhausting one at a time
REPEAT_DAILY = False     # if True, restart the full session each day at START_TIME

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

def run_call(NUMBER, attempt, total_calls):
    play_sound()
    notify("FaceTime Loop", f"Calling {NUMBER} (attempt {attempt})")
    subprocess.run(["open", f"facetime://{NUMBER}"])
    wait = random.uniform(DELAY, DELAY * 1.5) if DELAY_RANDOM else DELAY
    log(f"[{NUMBER}] Call {attempt} (total: {total_calls}). Next in {int(wait)}s...")
    time.sleep(wait)

def run_session():
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
    log(f"Session ended. Total calls made: {total_calls}")
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
