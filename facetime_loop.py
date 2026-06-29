import subprocess
import time
import sys

NUMBER = "+919324718705"
DELAY = 20  # seconds between calls
MAX_ATTEMPTS = 10  # set to None for unlimited

print(f"Calling {NUMBER} on FaceTime... Press Ctrl+C to stop.")
if MAX_ATTEMPTS:
    print(f"Will stop after {MAX_ATTEMPTS} attempts.")

attempt = 0
try:
    while True:
        if MAX_ATTEMPTS and attempt >= MAX_ATTEMPTS:
            print(f"\nReached {MAX_ATTEMPTS} attempts. Stopping.")
            break
        attempt += 1
        subprocess.run(["open", f"facetime://{NUMBER}"])
        print(f"Call {attempt} initiated. Next call in {DELAY} seconds...")
        time.sleep(DELAY)
except KeyboardInterrupt:
    print(f"\nStopped after {attempt} attempt(s).")
