import os
import sys
import time
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(base_dir, "pythoncode.py")
    try:
        subprocess.run([sys.executable, server_script])
    except KeyboardInterrupt:
        print(" ")

if __name__ == "__main__":
    main()
