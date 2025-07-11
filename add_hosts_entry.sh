#!/bin/bash
# Simple script to add entry to hosts file
# Usage: ./add_hosts_entry.sh
HOST_IP="172.18.0.4"
HOST_NAME="calculator.local"
HOST_ENTRY="$HOST_IP $HOST_NAME"

# Get hosts file path based on OS
case "$(uname -s)" in
    Linux*|Darwin*)
        HOSTS_FILE="/etc/hosts"
        USE_SUDO=true
        ;;
    CYGWIN*|MINGW*|MSYS*)
        HOSTS_FILE="C:\\Windows\\System32\\drivers\\etc\\hosts"
        USE_SUDO=false
        ;;
    *)
        echo "Unsupported OS"
        exit 1
        ;;
esac

# Check if entry already exists
if [[ -f "$HOSTS_FILE" ]] && grep -q "$HOST_NAME" "$HOSTS_FILE"; then
    echo "Entry for $HOST_NAME already exists in hosts file"
    exit 0
fi

# Add new entry
echo "Adding entry: $HOST_ENTRY"
if [[ "$USE_SUDO" == true ]]; then
    echo "$HOST_ENTRY" | sudo tee -a "$HOSTS_FILE" > /dev/null
else
    echo "$HOST_ENTRY" >> "$HOSTS_FILE"
fi

echo "✅ Done! You can now use '$HOST_NAME' to access $HOST_IP"