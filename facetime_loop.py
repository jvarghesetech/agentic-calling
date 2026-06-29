import subprocess
import time
import sys

NUMBER = "+919324718705"
DELAY = 20  # seconds between calls

print(f"Calling {NUMBER} on FaceTime... Press Ctrl+C to stop.")

try:
    while True:
        subprocess.run(["open", f"facetime://{NUMBER}"])
        print(f"Call initiated. Next call in {DELAY} seconds...")
        time.sleep(DELAY)
except KeyboardInterrupt:
    print("\nStopped.")
