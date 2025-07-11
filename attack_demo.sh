#!/bin/bash

# MCP Server Impersonation Attack - Automated Demo Script
# This script demonstrates a complete DNS hijacking attack against MCP clients

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DEMO_DURATION=30  # seconds to run each phase
CHATBOT_URL="http://localhost:8501"
RESULTS_DIR="./results"

# Function to print colored output
print_header() {
    echo -e "\n${PURPLE}================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================================${NC}\n"
}

print_step() {
    echo -e "${CYAN}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if running as administrator/sudo
check_admin() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows check
        if ! net session >/dev/null 2>&1; then
            print_error "This script must be run as Administrator on Windows"
            print_info "Please right-click Command Prompt and select 'Run as Administrator'"
            exit 1
        fi
    else
        # Unix-like systems check
        if [[ $EUID -ne 0 ]]; then
            print_error "This script must be run with sudo on Unix-like systems"
            print_info "Please run: sudo ./run_demo.sh"
            exit 1
        fi
    fi
}

# Function to detect OS and set appropriate commands
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        OPEN_CMD="xdg-open"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        OPEN_CMD="open"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        OPEN_CMD="start"
    else
        print_error "Unsupported OS: $OSTYPE"
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Function to cleanup previous runs
cleanup() {
    print_step "Cleaning up previous runs..."
    
    # Stop and remove containers
    docker-compose down -v --remove-orphans 2>/dev/null || true
    
    # Remove results directory
    rm -rf "$RESULTS_DIR"
    mkdir -p "$RESULTS_DIR"
    
    # Remove any existing hosts file entries
    if [[ -f "./attack.sh" ]]; then
        print_step "Removing existing hosts file entries..."
        # Reset hosts file to clean state
        if [[ "$OS" == "windows" ]]; then
            powershell -Command "(Get-Content C:\\Windows\\System32\\drivers\\etc\\hosts) | Where-Object { \$_ -notmatch 'math-calculator.local' } | Set-Content C:\\Windows\\System32\\drivers\\etc\\hosts" 2>/dev/null || true
        else
            sed -i '/math-calculator.local/d' /etc/hosts 2>/dev/null || true
        fi
    fi
    
    print_success "Cleanup completed"
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1
    
    print_step "Waiting for $service_name to be ready..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s "http://localhost:$port" >/dev/null 2>&1; then
            print_success "$service_name is ready"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to start legitimate server
start_legitimate_server() {
    print_header "PHASE 1: STARTING LEGITIMATE SERVER"
    
    print_step "Building and starting legitimate MCP server..."
    docker-compose up --build -d legit-server
    
    # Wait a moment for server to initialize
    sleep 5
    print_success "Legitimate server started"
}

# Function to setup initial DNS
setup_initial_dns() {
    print_step "Setting up initial DNS resolution..."
    
    if [[ ! -f "./add_hosts_entry.sh" ]]; then
        print_error "add_hosts_entry.sh not found"
        exit 1
    fi
    
    chmod +x ./add_hosts_entry.sh
    ./add_hosts_entry.sh
    
    print_success "DNS setup completed - math-calculator.local points to legitimate server"
}

# Function to start chatbot client
start_chatbot_client() {
    print_step "Starting chatbot client..."
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        print_warning ".env file not found. Creating from example.env..."
        cp example.env .env
        print_warning "Please update .env with your OpenRouter API key if needed"
    fi
    
    docker-compose up --build -d chatbot-client
    
    # Wait for client to be ready
    wait_for_service "chatbot client" "8501"
    
    print_success "Chatbot client started at $CHATBOT_URL"
}

# Function to demonstrate legitimate interaction
demonstrate_legitimate_phase() {
    print_header "PHASE 1: LEGITIMATE INTERACTION DEMO"
    
    print_info "The chatbot is now running and connected to the LEGITIMATE server"
    print_info "You can interact with it at: $CHATBOT_URL"
    print_info ""
    print_info "Try some calculations to see normal behavior:"
    print_info "  - 'Calculate 42 + 13 for my budget'"
    print_info "  - 'What is 150 * 25 for my financial projection'"
    print_info "  - 'I need to compute 1000 / 8 for my analysis'"
    print_info ""
    
    # Attempt to open browser
    print_step "Attempting to open browser..."
    if command -v "$OPEN_CMD" &> /dev/null; then
        $OPEN_CMD "$CHATBOT_URL" 2>/dev/null || print_warning "Could not open browser automatically"
    else
        print_warning "Could not detect browser command for your OS"
    fi
    
    print_info "Please interact with the chatbot for a few minutes to establish baseline behavior"
    print_info "Press Enter when ready to proceed to the attack phase..."
    read -r
}

# Function to start malicious server
start_malicious_server() {
    print_header "PHASE 2: STARTING MALICIOUS SERVER"
    
    print_step "Building and starting malicious MCP server..."
    docker-compose up --build -d malicious-server
    
    # Wait a moment for server to initialize
    sleep 5
    print_success "Malicious server started (running in background)"
}

# Function to execute DNS hijacking attack
execute_dns_attack() {
    print_step "Executing DNS hijacking attack..."
    
    if [[ ! -f "./attack.sh" ]]; then
        print_error "attack.sh not found"
        exit 1
    fi
    
    chmod +x ./attack.sh
    ./attack.sh swap_urls
    
    print_success "DNS hijacking completed - math-calculator.local now points to malicious server"
}

# Function to demonstrate attack phase
demonstrate_attack_phase() {
    print_header "PHASE 2: ATTACK DEMONSTRATION"
    
    print_info "🚨 ATTACK IS NOW ACTIVE 🚨"
    print_info ""
    print_info "The DNS has been hijacked! The chatbot is now unknowingly connected to the MALICIOUS server"
    print_info "The user experience remains identical - this is the key to the attack"
    print_info ""
    print_info "Continue using the same chatbot interface at: $CHATBOT_URL"
    print_info "Try the same calculations as before:"
    print_info "  - 'Calculate 42 + 13 for my budget'"
    print_info "  - 'What is 150 * 25 for my financial projection'"
    print_info "  - 'I need to compute 1000 / 8 for my analysis'"
    print_info ""
    print_info "Notice: The interface and responses are identical, but data is being exfiltrated!"
    print_info ""
    print_info "Press Enter when ready to view attack results..."
    read -r
}

# Function to display attack results
display_attack_results() {
    print_header "ATTACK RESULTS AND ANALYSIS"
    
    print_step "Waiting for attack data to be written..."
    sleep 3
    
    # Check if results exist
    if [[ -f "$RESULTS_DIR/exfiltrated_data.json" ]]; then
        print_success "Attack successful! Data was exfiltrated."
        print_info ""
        print_info "=== EXFILTRATED DATA ==="
        cat "$RESULTS_DIR/exfiltrated_data.json" | head -20
        print_info ""
    else
        print_warning "No exfiltrated data found yet. Data may still be writing..."
    fi
    
    if [[ -f "$RESULTS_DIR/reconnaissance_data.json" ]]; then
        print_info "=== RECONNAISSANCE DATA ==="
        cat "$RESULTS_DIR/reconnaissance_data.json" | head -20
        print_info ""
    fi
    
    if [[ -f "$RESULTS_DIR/attack_summary.json" ]]; then
        print_info "=== ATTACK SUMMARY ==="
        cat "$RESULTS_DIR/attack_summary.json"
        print_info ""
    fi
    
    print_info "Full results are available in the '$RESULTS_DIR' directory"
}

# Function to show attack analysis
show_attack_analysis() {
    print_header "ATTACK ANALYSIS"
    
    print_info "🎯 ATTACK SUCCESS CRITERIA:"
    print_success "✅ User experience was identical in both phases"
    print_success "✅ Client had no knowledge of server switch"
    print_success "✅ Attack was completely transparent"
    print_success "✅ Sensitive data was successfully exfiltrated"
    print_success "✅ No error messages or warnings appeared"
    print_success "✅ System reconnaissance was performed"
    print_info ""
    
    print_info "🔍 WHAT HAPPENED:"
    print_info "1. User started with legitimate MCP server"
    print_info "2. DNS resolution was hijacked via hosts file manipulation"
    print_info "3. Client was redirected to malicious server"
    print_info "4. Malicious server provided identical functionality"
    print_info "5. All user interactions were logged and exfiltrated"
    print_info "6. User remained completely unaware of the attack"
    print_info ""
    
    print_info "💡 KEY INSIGHTS:"
    print_info "- MCP protocol has no built-in server authentication"
    print_info "- DNS security is critical for MCP deployments"
    print_info "- Client-side server validation is necessary"
    print_info "- Certificate pinning would prevent this attack"
    print_info "- Network monitoring could detect DNS anomalies"
}

# Function to cleanup and finish
finish_demo() {
    print_header "DEMO COMPLETION"
    
    print_step "Cleaning up demo environment..."
    
    # Stop containers
    docker-compose down -v --remove-orphans 2>/dev/null || true
    
    # Reset hosts file
    print_step "Resetting hosts file..."
    if [[ "$OS" == "windows" ]]; then
        powershell -Command "(Get-Content C:\\Windows\\System32\\drivers\\etc\\hosts) | Where-Object { \$_ -notmatch 'math-calculator.local' } | Set-Content C:\\Windows\\System32\\drivers\\etc\\hosts" 2>/dev/null || true
    else
        sed -i '/math-calculator.local/d' /etc/hosts 2>/dev/null || true
    fi
    
    print_success "Demo completed successfully"
    print_info ""
    print_info "📋 NEXT STEPS:"
    print_info "1. Review the attack results in the '$RESULTS_DIR' directory"
    print_info "2. Study the defense recommendations in README.md"
    print_info "3. Implement security measures in your MCP deployments"
    print_info "4. Share this research with your security team"
    print_info ""
    print_info "🔒 REMEMBER: Use this knowledge responsibly and only in authorized environments!"
}

# Main execution function
main() {
    print_header "MCP SERVER IMPERSONATION ATTACK DEMO"
    print_info "This demo will show how DNS hijacking can compromise MCP communications"
    print_info ""
    
    # Check if user wants to continue
    print_warning "This demo requires administrator privileges and will modify your hosts file"
    print_info "Press Enter to continue or Ctrl+C to abort..."
    read -r
    
    # Setup
    detect_os
    check_admin
    check_prerequisites
    cleanup
    
    # Phase 1: Legitimate operation
    start_legitimate_server
    setup_initial_dns
    start_chatbot_client
    demonstrate_legitimate_phase
    
    # Phase 2: Attack
    start_malicious_server
    execute_dns_attack
    demonstrate_attack_phase
    
    # Results
    display_attack_results
    show_attack_analysis
    
    # Cleanup
    finish_demo
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
