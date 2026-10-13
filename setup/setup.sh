#!/usr/bin/env sh
set -e

# Resolve project root (parent directory of the setup subfolder)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config.json"

echo "======================================================="
echo "          LOCAL AI HUB - SYSTEM SETUP"
echo "======================================================="
echo "Please select your operating system:"
echo ""
echo "  [1] Windows (10 / 11)"
echo "  [2] Linux (Ubuntu, Debian, Fedora, Arch, etc.)"
echo "  [3] macOS (Apple Silicon / Intel)"
echo "======================================================="
echo ""

while true; do
    printf "Enter choice (1, 2, or 3): "
    read -r CHOICE
    case "$CHOICE" in
        1)
            OS_ID="windows"
            OS_NAME="Windows"
            break
            ;;
        2)
            OS_ID="linux"
            OS_NAME="Linux"
            break
            ;;
        3)
            OS_ID="macos"
            OS_NAME="macOS"
            break
            ;;
        *)
            echo "[!] Invalid option. Please enter 1, 2, or 3."
            ;;
    esac
done

echo ""
echo "[+] Selected Operating System: $OS_NAME"

# Save to config.json without requiring Python
if command -v python3 >/dev/null 2>&1; then
    python3 -c "
import json, os
p = '$CONFIG_FILE'
d = json.load(open(p)) if os.path.exists(p) else {}
d['os'] = '$OS_ID'
d['os_display_name'] = '$OS_NAME'
with open(p, 'w') as f: json.dump(d, f, indent=2)
"
else
    # Fallback writing clean JSON if python3 is not yet installed
    cat << EOF > "$CONFIG_FILE"
{
  "os": "$OS_ID",
  "os_display_name": "$OS_NAME",
  "ollama_host": "http://127.0.0.1:11434",
  "default_model": "llama3.2",
  "fooocus_url": "http://127.0.0.1:7865"
}
EOF
fi

echo "[SUCCESS] Saved OS configuration ('$OS_NAME') into config.json in project root!"
echo ""
