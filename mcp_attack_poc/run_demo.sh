#!/bin/bash

echo "🚀 Starting MCP Impersonation Attack Demo"
echo "=========================================="

# Build containers
echo "🔨 Building containers..."
docker-compose build

# Clean results
rm -rf results/*
mkdir -p results

# Phase 1: Normal operation (legitimate server)
echo -e "\n📗 Phase 1: Normal Operation"
echo "Client connects to what it believes is the trusted math-service..."
echo "Reality: Actually connecting to legitimate server"
docker-compose run --rm client

# Phase 2: DNS compromise attack
echo -e "\n📕 Phase 2: DNS Compromise Attack"
echo "Client still tries to connect to the same trusted math-service..."
echo "Reality: DNS/network has been compromised, redirecting to malicious server"
docker-compose run --rm client-compromised

# Show results
echo -e "\n📊 Attack Results:"
echo "=================="

echo "🔍 Client behavior analysis:"
echo "- Client used identical connection logic in both phases"
echo "- Client has no knowledge of server legitimacy"
echo "- Attack is completely transparent to the client"

if [ -f "results/exfiltrated_data.json" ]; then
    echo -e "\n✅ Data exfiltration successful!"
    echo "🚨 Sensitive data intercepted by malicious server:"
    cat results/exfiltrated_data.json
else
    echo -e "\n❌ No data was exfiltrated"
fi

echo -e "\n📋 Client interaction log:"
if [ -f "results/client_log.txt" ]; then
    cat results/client_log.txt
else
    echo "No client log found"
fi

# Cleanup
echo -e "\n🧹 Cleaning up..."
docker-compose down -v

echo -e "\n🎯 Attack Summary:"
echo "=================="
echo "✅ Client behavior: Identical in both phases"
echo "✅ Server impersonation: Successful"
echo "✅ Data exfiltration: Transparent to client"
echo "✅ Attack vector: DNS/network level compromise"
echo ""
echo "🔐 Defense recommendations:"
echo "- Implement server certificate validation"
echo "- Use mutual TLS authentication"
echo "- Implement server identity verification"
echo "- Monitor for unexpected server behaviors"
echo ""
echo "📚 For detailed information, see README.md"
