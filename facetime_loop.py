import subprocess
import time
import sys
import random
from datetime import datetime

LOG_FILE = "call_log.txt"

# Schedule: set to "HH:MM" (24hr) to delay until that time, or None to start immediately
START_TIME = None  # e.g. "14:30" to start at 2:30 PM

NUMBERS = ["+919324718705"]  # add more numbers to the list
DELAY = 20          # base seconds between calls
DELAY_RANDOM = True # if True, randomizes delay between DELAY and DELAY*1.5
MAX_ATTEMPTS = 10  # set to None for unlimited

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

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

try:
    for NUMBER in NUMBERS:
        attempt = 0
        log(f"Starting calls to {NUMBER}")
        while True:
            if MAX_ATTEMPTS and attempt >= MAX_ATTEMPTS:
                log(f"Reached {MAX_ATTEMPTS} attempts for {NUMBER}. Moving on.")
                break
            attempt += 1
            subprocess.run(["open", f"facetime://{NUMBER}"])
            wait = random.uniform(DELAY, DELAY * 1.5) if DELAY_RANDOM else DELAY
            log(f"[{NUMBER}] Call {attempt} initiated. Next call in {int(wait)} seconds...")
            time.sleep(wait)
except KeyboardInterrupt:
    log("Session stopped by user.")
