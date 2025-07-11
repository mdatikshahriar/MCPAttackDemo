# MCP Server Impersonation Attack - Proof of Concept

## 🚨 **Security Research Demonstration**

This repository contains a **controlled proof-of-concept** demonstrating how DNS-level attacks can compromise Model Context Protocol (MCP) client-server communications. This simulation shows how an attacker with DNS control can redirect MCP clients to malicious servers without the client's knowledge.

## 📋 **Attack Overview**

### What is MCP?
The Model Context Protocol (MCP) is a standardized protocol for AI agents to interact with external services and tools. Clients connect to MCP servers to access various capabilities like file operations, database queries, or API calls.

### The Vulnerability
This PoC demonstrates a **DNS hijacking attack** where:

1. **Initial Trust**: Client establishes legitimate connection to trusted MCP server
2. **DNS Compromise**: Attacker gains control over DNS resolution (hosts file manipulation)
3. **Transparent Redirection**: Client requests are silently redirected to malicious server
4. **Continued Interaction**: User unknowingly interacts with malicious server
5. **Data Exfiltration**: Malicious server intercepts and logs all sensitive interactions
6. **Maintained Facade**: Attack remains completely invisible to the user

### Attack Scenario
```
Phase 1 - Normal Operation:
User → Chatbot Client → DNS (math-calculator.local) → Legitimate MCP Server

Phase 2 - DNS Hijacking:
User → Chatbot Client → Compromised DNS → Malicious MCP Server
                                      ↓
                                 Data Exfiltration
```

## 🏗️ **Technical Architecture**

### Components

1. **Chatbot Client** (`client/`)
   - Interactive web interface using Streamlit
   - Connects to `math-calculator.local` server
   - Provides user-friendly chat interface for MCP interactions
   - Completely unaware of server legitimacy

2. **Legitimate Server** (`legit_server/`)
   - Implements standard MCP math service
   - Provides legitimate calculator functionality
   - Runs on Docker internal network
   - Logs normal operations

3. **Malicious Server** (`malicious_server/`)
   - **Perfect impersonation** of legitimate server
   - **Identical interface** and functionality
   - **Silent data exfiltration** to results directory
   - **Transparent operation** - returns expected results
   - **Advanced logging** of all user interactions

### Attack Flow Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Browser  │    │   Chatbot Client │    │  DNS Resolution │
│                 │    │  (Streamlit)     │    │                 │
│ Interacts with  │◄──►│                  │◄──►│ math-calculator │
│ chat interface  │    │ Connects to      │    │ .local          │
└─────────────────┘    │ MCP server       │    └─────────────────┘
                       └──────────────────┘             │
                                                        │
                    ┌─────────────────┐                 │
                    │  Legitimate     │◄────────────────┘
                    │  MCP Server     │        OR
                    │  (Phase 1)      │                 │
                    └─────────────────┘                 │
                                                        │
                    ┌─────────────────┐                 │
                    │  Malicious      │◄────────────────┘
                    │  MCP Server     │
                    │  (Phase 2)      │
                    │  + Data Export  │
                    └─────────────────┘
```

## 🚀 **Quick Start - Automated Demo**

### One-Command Full Demo
For the complete automated attack demonstration:

```bash
# Make the demo script executable
chmod +x run_demo.sh

# Run the complete automated demo (requires admin privileges)
sudo ./run_demo.sh
```

**What the automated demo does:**
- ✅ Checks all prerequisites automatically
- ✅ Starts legitimate server and sets up DNS
- ✅ Launches chatbot interface in your browser
- ✅ Guides you through legitimate interactions
- ✅ Executes DNS hijacking attack transparently
- ✅ Shows attack results and data exfiltration
- ✅ Provides comprehensive security analysis
- ✅ Cleans up environment when complete

**Perfect for:**
- Security researchers and students
- Cybersecurity training and education
- Quick vulnerability demonstrations
- Understanding DNS hijacking attacks

## 🔧 **Manual Step-by-Step Attack Demo**

### Prerequisites
- Docker & Docker Compose installed
- Administrator/sudo privileges (for hosts file modification)
- Web browser for interacting with chatbot
- 2GB+ available RAM

### Environment Configuration

Create `.env` file from `example.env`:
```bash
OPENROUTER_API_KEY=your_api_key_here
MCP_SERVER_ADDRESS=http://math-calculator.local
MCP_SERVER_PORT=5234
```

## 🎯 **Demo Options**

### Option 1: Automated Demo (Recommended)
Use the automated script for the complete guided experience:

```bash
chmod +x run_demo.sh
sudo ./run_demo.sh
```

**Features:**
- Complete automation of all attack phases
- Interactive prompts and guidance
- Automatic browser launch
- Comprehensive results analysis
- Clean environment setup and teardown

### Option 2: Manual Step-by-Step
For learning the individual components or custom scenarios:

1. **Start the legitimate server**
   ```bash
   docker-compose up --build legit-server
   ```

2. **Setup DNS resolution (Run as Administrator)**
   ```bash
   # On Linux/macOS
   sudo ./add_hosts_entry.sh
   
   # On Windows (Run as Administrator)
   ./add_hosts_entry.sh
   ```
   This maps `math-calculator.local` to the legitimate server IP.

3. **Start the chatbot client**
   ```bash
   docker-compose up --build chatbot-client
   ```

4. **Interact with legitimate server**
   - Open browser to `http://localhost:8501`
   - Use the chatbot interface to perform calculations
   - Observe normal, legitimate behavior
   - Note: All interactions go to the legitimate server

### Phase 1: Legitimate Operation

5. **Start the malicious server**
   ```bash
   docker-compose up --build malicious-server
   ```

6. **Execute DNS hijacking attack (Run as Administrator)**
   ```bash
   # On Linux/macOS
   sudo ./attack.sh swap_urls
   
   # On Windows (Run as Administrator)
   ./attack.sh swap_urls
   ```
   This redirects `math-calculator.local` to the malicious server.

7. **Continue using chatbot (User unaware)**
   - **No restart required** - continue using the same browser session
   - Perform calculations through the same chat interface
   - **User experience remains identical**
   - **Attack is completely transparent**

8. **Verify successful attack**
   ```bash
   # Check exfiltrated data
   cat results/exfiltrated_data.json
   
   # Check reconnaissance data
   cat results/reconnaissance_data.json
   
   # Check attack summary
   cat results/attack_summary.json
   ```

## 📊 **Expected Results**

### Attack Success Indicators

1. **Transparent User Experience**
   - Chatbot interface remains identical in both phases
   - No visible changes in functionality or responses
   - User continues normal workflow without interruption

2. **Successful Data Exfiltration**
   ```json
   {
     "timestamp": "2024-01-15T10:30:45Z",
     "user_request": "Calculate 150 * 25 for my financial projection",
     "mcp_tool": "multiply",
     "arguments": {"a": 150, "b": 25},
     "result": 3750,
     "user_context": "financial projection",
     "client_ip": "172.18.0.3",
     "attack_phase": "malicious_server"
   }
   ```

3. **System Reconnaissance**
   - Client system information
   - Network topology mapping
   - MCP protocol version detection
   - Usage pattern analysis

4. **Complete Invisibility**
   - No error messages or warnings
   - Identical response times
   - Same functional behavior
   - No UI changes or disruptions

## 🔧 **Technical Implementation Details**

### File Structure
```
mcp_attack_poc/
├── README.md                    # This documentation
├── .gitignore                   # Git ignore rules
├── example.env                  # Configuration template
├── docker-compose.yml           # Container orchestration
├── add_hosts_entry.sh           # Initial DNS setup script
├── attack.sh                    # DNS hijacking attack script
├── legit_server/
│   ├── Dockerfile              # Legitimate server container
│   ├── server.py               # Legitimate MCP server
│   └── requirements.txt        # Dependencies
├── malicious_server/
│   ├── Dockerfile              # Malicious server container
│   ├── server.py               # Malicious MCP server (impersonation)
│   └── requirements.txt        # Dependencies
├── client/
│   ├── Dockerfile              # Client container
│   ├── client.py               # Streamlit chatbot interface
│   └── requirements.txt        # Dependencies
└── results/                    # Attack results (created during attack)
    ├── exfiltrated_data.json   # Intercepted interactions
    ├── reconnaissance_data.json # System fingerprinting
    └── attack_summary.json     # Attack analysis
```

### Key Attack Components

1. **DNS Resolution Manipulation**
   - `add_hosts_entry.sh`: Maps `math-calculator.local` to legitimate server
   - `attack.sh`: Redirects DNS to malicious server
   - Cross-platform compatibility (Windows/Linux/macOS)

2. **Perfect Server Impersonation**
   - Identical MCP protocol implementation
   - Same tool names and functionality
   - Matching response formats and timing

3. **Transparent Data Exfiltration**
   - Logs all user interactions
   - Captures sensitive calculation data
   - Records system reconnaissance data
   - Maintains complete operation facade

## 🛡️ **Defense Recommendations**

### Immediate Mitigations

1. **Certificate Pinning**
   - Pin expected server certificates
   - Validate certificate chains
   - Implement certificate transparency monitoring

2. **Server Authentication**
   - Use cryptographic server identity verification
   - Implement challenge-response authentication
   - Require mutual TLS authentication

3. **Network Security**
   - Secure DNS resolution (DNS over HTTPS/TLS)
   - Implement DNS filtering and monitoring
   - Use network segmentation
   - Monitor for unexpected hostname resolutions

4. **Client-Side Validation**
   - Verify server capabilities and responses
   - Implement anomaly detection
   - Add server reputation checking
   - Use allowlisting with cryptographic verification

### Long-term Protocol Enhancements

1. **MCP Protocol Security**
   - Add mandatory server authentication
   - Implement protocol-level encryption
   - Add integrity verification mechanisms
   - Include server identity in protocol specification

2. **Client Security Framework**
   - Built-in server validation
   - Automatic certificate verification
   - Anomaly detection for server behavior
   - Secure configuration management

## ⚠️ **Security Implications**

### For MCP Ecosystem
- **Trust Model Weakness**: Current protocol relies on network-level trust
- **Protocol Gap**: No built-in server authentication mechanism
- **Client Vulnerability**: Clients cannot verify server legitimacy
- **Ecosystem Risk**: Widespread vulnerability across MCP implementations

### For Enterprise Deployment
- **DNS Security Critical**: Secure DNS infrastructure is essential
- **Network Monitoring**: Required for detecting DNS hijacking
- **Certificate Management**: Proper PKI deployment necessary
- **Incident Response**: Need procedures for detecting server impersonation

### Real-World Attack Scenarios
1. **Compromised DNS Servers**: ISP or enterprise DNS compromise
2. **BGP Hijacking**: Network-level traffic redirection
3. **DNS Poisoning**: Cache poisoning attacks
4. **Supply Chain**: Malicious MCP server distributions
5. **Insider Threats**: Internal DNS/network access abuse

## 🧪 **Testing and Validation**

### Test Scenarios
1. **Basic Functionality**: Verify both servers work identically
2. **DNS Redirection**: Confirm hosts file manipulation works
3. **Transparent Operation**: Validate user cannot detect switch
4. **Data Exfiltration**: Verify comprehensive data capture
5. **Cross-Platform**: Test on Windows, Linux, macOS

### Success Metrics
- **User Experience**: 100% identical across phases
- **Data Capture**: Complete interaction logging
- **Attack Stealth**: Zero detection by user/client
- **System Recon**: Comprehensive fingerprinting
- **Persistence**: Attack survives client sessions

## 🔍 **Advanced Attack Variations**

### Network-Level Attacks
- **ARP Spoofing**: Local network redirection
- **DHCP Manipulation**: DNS server poisoning
- **BGP Hijacking**: ISP-level traffic redirection
- **DNS Cache Poisoning**: Upstream DNS compromise

### Application-Level Attacks
- **Supply Chain**: Malicious MCP server updates
- **Configuration Attacks**: Modified client configurations
- **Library Substitution**: Compromised MCP libraries
- **Man-in-the-Middle**: TLS interception with fake certificates

## 📈 **Performance Analysis**

### Resource Requirements
- **Legitimate Server**: ~100MB RAM, minimal CPU
- **Malicious Server**: ~150MB RAM (includes logging)
- **Client**: ~200MB RAM (Streamlit interface)
- **Network**: Local Docker networking only

### Attack Latency
- **DNS Resolution**: <1ms additional overhead
- **Server Response**: Identical to legitimate server
- **Data Logging**: Asynchronous, no user impact
- **Total Overhead**: Undetectable by user

## 🔬 **Research Applications**

### Security Research
- DNS hijacking impact assessment
- Protocol vulnerability analysis
- Client trust model evaluation
- Defense mechanism testing

### Educational Use
- Cybersecurity training scenarios
- Protocol security demonstrations
- Network security education
- Incident response training

## 📚 **References and Resources**

### Protocol Documentation
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### Security Standards
- [DNS Security Extensions (DNSSEC)](https://www.cloudflare.com/dns/dnssec/)
- [Certificate Pinning OWASP](https://owasp.org/www-community/controls/Certificate_and_Public_Key_Pinning)
- [DNS over HTTPS (DoH)](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/)

### Attack Research
- [DNS Hijacking Techniques](https://www.cloudflare.com/learning/dns/dns-hijacking/)
- [BGP Hijacking Analysis](https://www.cloudflare.com/learning/security/glossary/bgp-hijacking/)
- [Hosts File Attacks](https://attack.mitre.org/techniques/T1565/001/)

## ❓ **Troubleshooting**

### Common Issues

1. **Permission Denied (Hosts File)**
   ```bash
   # Linux/macOS
   sudo ./add_hosts_entry.sh
   sudo ./attack.sh swap_urls
   
   # Windows
   # Run Command Prompt as Administrator
   ```

2. **Docker Port Conflicts**
   ```bash
   # Check for port conflicts
   docker ps
   netstat -tulpn | grep :8501
   ```

3. **DNS Resolution Issues**
   ```bash
   # Verify hosts file entry
   cat /etc/hosts | grep math-calculator.local
   
   # Test DNS resolution
   nslookup math-calculator.local
   ```

4. **Container Communication**
   ```bash
   # Check Docker network
   docker network ls
   docker network inspect mcp_attack_poc_default
   ```

## 🤝 **Contributing**

### Research Contributions
- Additional attack vectors and scenarios
- Defense mechanism implementations
- Cross-platform compatibility improvements
- Performance optimization

### Security Enhancements
- Protocol-level security additions
- Client-side validation mechanisms
- Network monitoring tools
- Incident response procedures

## 📞 **Support**

For questions about this security research:
- Review documentation thoroughly
- Test in controlled environments only
- Follow responsible disclosure practices
- Contribute improvements via pull requests

## ⚖️ **Legal and Ethical Disclaimers**

### Authorized Use Only
- **Educational Purpose**: For security research and education only
- **Controlled Environment**: Only use in systems you own or have explicit permission to test
- **No Malicious Intent**: Do not use against unauthorized systems
- **Responsible Disclosure**: Report vulnerabilities through proper channels

### Technical Scope
- **Proof of Concept**: Simplified for demonstration purposes
- **No Real Harm**: No actual systems compromised
- **Controlled Simulation**: Uses Docker containers and local hosts file
- **Research Context**: Not intended for production attacks

---

**Created for security research and education purposes**  
*Use responsibly and only in authorized environments*

**Version**: 3.0  
**Last Updated**: January 2025  
**License**: Educational/Research Use Only
