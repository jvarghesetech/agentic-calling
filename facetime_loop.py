import subprocess
import time
import sys
from datetime import datetime

LOG_FILE = "call_log.txt"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

NUMBERS = ["+919324718705"]  # add more numbers to the list
DELAY = 20  # seconds between calls
MAX_ATTEMPTS = 10  # set to None for unlimited

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
            log(f"[{NUMBER}] Call {attempt} initiated. Next call in {DELAY} seconds...")
            time.sleep(DELAY)
except KeyboardInterrupt:
    log("Session stopped by user.")
