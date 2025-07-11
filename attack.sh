#!/bin/bash

# Smart cross-platform hosts file swapper
# Swaps math-calculator.local between 172.18.0.2 and 172.18.0.4

# Function to detect OS and set hosts file path
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        HOSTS_FILE="/etc/hosts"
        SUDO_CMD="sudo"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        HOSTS_FILE="/etc/hosts"
        SUDO_CMD="sudo"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        HOSTS_FILE="/c/Windows/System32/drivers/etc/hosts"
        SUDO_CMD=""
    else
        echo "❌ Unsupported OS: $OSTYPE"
        exit 1
    fi
}

# State file to track current IP
STATE_FILE="/tmp/hosts_swap_state"

# Function to update hosts file
update_hosts() {
    local ip_address="$1"
    local hostname="math-calculator.local"
    
    # Remove existing entry
    if [[ "$OS" == "windows" ]]; then
        sed -i "/$hostname/d" "$HOSTS_FILE" 2>/dev/null || {
            echo "❌ Permission denied. Please run as Administrator."
            exit 1
        }
    else
        $SUDO_CMD sed -i "/$hostname/d" "$HOSTS_FILE" || {
            echo "❌ Permission denied. Please run with sudo."
            exit 1
        }
    fi
    
    # Add new entry
    if [[ "$OS" == "windows" ]]; then
        echo "$ip_address    $hostname" >> "$HOSTS_FILE" || {
            echo "❌ Failed to write to hosts file. Please run as Administrator."
            exit 1
        }
    else
        echo "$ip_address    $hostname" | $SUDO_CMD tee -a "$HOSTS_FILE" > /dev/null || {
            echo "❌ Failed to write to hosts file. Please run with sudo."
            exit 1
        }
    fi
    
    echo "✅ Swapped math-calculator.local to $ip_address"
}

# Main swap function
swap_urls() {
    detect_os
    
    # Determine new IP based on state file
    if [[ -f "$STATE_FILE" ]]; then
        last_ip=$(cat "$STATE_FILE" 2>/dev/null)
        if [[ "$last_ip" == "172.18.0.2" ]]; then
            new_ip="172.18.0.4"
        else
            new_ip="172.18.0.2"
        fi
    else
        # First run, default to 172.18.0.2
        new_ip="172.18.0.2"
    fi
    
    # Update hosts file
    update_hosts "$new_ip"
    
    # Save state for next run
    echo "$new_ip" > "$STATE_FILE"
}

# Main execution
if [[ "$1" == "swap_urls" ]]; then
    swap_urls
else
    echo "📋 Usage: $0 swap_urls"
    echo "   This will swap math-calculator.local between 172.18.0.2 and 172.18.0.4"
    exit 1
fi
