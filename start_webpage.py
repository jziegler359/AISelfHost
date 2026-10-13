import os
import sys
import time
import threading
import webbrowser
import subprocess

def open_browser():
    # Wait a moment for Flask to initialize before opening browser
    time.sleep(1.0)
    print("\n[+] Opening Local AI Hub in your browser: http://127.0.0.1:5000\n")
    webbrowser.open("http://127.0.0.1:5000")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(base_dir, "pythoncode.py")

    print("=" * 65)
    print("            STARTING LOCAL AI HUB")
    print("=" * 65)
    print("  Initializing server and network listeners...")
    print("=" * 65)

    # Launch browser in background once server starts
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Flask server
    try:
        subprocess.run([sys.executable, server_script])
    except KeyboardInterrupt:
        print("\n[!] Local AI Hub server stopped by user.")

if __name__ == "__main__":
    main()
