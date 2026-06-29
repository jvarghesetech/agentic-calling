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

NUMBERS = ["+919324718705"]  # add more numbers to the list
DELAY = 20          # base seconds between calls
DELAY_RANDOM = True # if True, randomizes delay between DELAY and DELAY*1.5
MAX_ATTEMPTS = 10   # set to None for unlimited
NUMBER_COOLDOWN = 30  # seconds to wait before moving to next number
MAX_DAILY_CALLS = 50  # hard cap on total calls per session, set to None for unlimited

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

if START_TIME:
    wait_until(START_TIME)

log(f"Session started. Calling {len(NUMBERS)} number(s) on FaceTime.")
if MAX_ATTEMPTS:
    log(f"Will stop after {MAX_ATTEMPTS} attempts per number.")
if MAX_DAILY_CALLS:
    log(f"Daily cap: {MAX_DAILY_CALLS} total calls.")

total_calls = 0

try:
    for i, NUMBER in enumerate(NUMBERS):
        if MAX_DAILY_CALLS and total_calls >= MAX_DAILY_CALLS:
            log(f"Daily cap of {MAX_DAILY_CALLS} calls reached. Stopping.")
            break
        if i > 0 and NUMBER_COOLDOWN:
            log(f"Cooldown: waiting {NUMBER_COOLDOWN}s before next number...")
            time.sleep(NUMBER_COOLDOWN)
        attempt = 0
        log(f"Starting calls to {NUMBER}")
        while True:
            if MAX_ATTEMPTS and attempt >= MAX_ATTEMPTS:
                log(f"Reached {MAX_ATTEMPTS} attempts for {NUMBER}. Moving on.")
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
            subprocess.run(["open", f"facetime://{NUMBER}"])
            wait = random.uniform(DELAY, DELAY * 1.5) if DELAY_RANDOM else DELAY
            log(f"[{NUMBER}] Call {attempt} initiated (total: {total_calls}). Next call in {int(wait)}s...")
            time.sleep(wait)
except StopIteration:
    pass
except KeyboardInterrupt:
    log(f"Session stopped by user after {total_calls} total call(s).")
