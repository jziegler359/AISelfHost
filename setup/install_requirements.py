import sys
import subprocess

REQUIRED_PACKAGES = [
    "flask",
    "flask-cors",
    "ollama",
    "requests",
    "gradio_client"
]

def install_packages():
    print("=" * 60)
    print("    Local AI Hub - Python Dependency Installer")
    print("=" * 60)
    print(f"Python interpreter: {sys.executable}\n")

    for package in REQUIRED_PACKAGES:
        print(f"-> Installing / Verifying {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   [OK] {package} ready.\n")
        except subprocess.CalledProcessError as e:
            print(f"   [ERROR] Failed to install {package}: {e}\n")
            sys.exit(1)

    print("=" * 60)
    print(" [SUCCESS] All packages successfully verified and installed!")
    print("=" * 60)

if __name__ == "__main__":
    install_packages()
