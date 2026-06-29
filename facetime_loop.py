import subprocess
import time
import sys

NUMBERS = ["+919324718705"]  # add more numbers to the list
DELAY = 20  # seconds between calls
MAX_ATTEMPTS = 10  # set to None for unlimited

print(f"Calling {len(NUMBERS)} number(s) on FaceTime... Press Ctrl+C to stop.")
if MAX_ATTEMPTS:
    print(f"Will stop after {MAX_ATTEMPTS} attempts per number.")

try:
    for NUMBER in NUMBERS:
        attempt = 0
        print(f"\nStarting calls to {NUMBER}")
        while True:
            if MAX_ATTEMPTS and attempt >= MAX_ATTEMPTS:
                print(f"Reached {MAX_ATTEMPTS} attempts for {NUMBER}. Moving on.")
                break
            attempt += 1
            subprocess.run(["open", f"facetime://{NUMBER}"])
            print(f"[{NUMBER}] Call {attempt} initiated. Next call in {DELAY} seconds...")
            time.sleep(DELAY)
except KeyboardInterrupt:
    print(f"\nStopped.")
