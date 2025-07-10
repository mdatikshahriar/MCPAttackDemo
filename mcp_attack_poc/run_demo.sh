#!/bin/bash

echo "🚀 Starting MCP Impersonation Attack Demo"
echo "=========================================="

# Build containers
echo "🔨 Building containers..."
docker-compose build

# ... (rest of the script remains the same)

# Run the chatbot demo
echo -e "\n💬 Starting Chatbot Demo"
echo "Access the chatbot at http://localhost:8501"
docker-compose up chatbot-client
