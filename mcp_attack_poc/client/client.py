import asyncio
import logging
import os
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Client ALWAYS believes it's connecting to the legitimate math-service
    # The server path is resolved by the "DNS" (docker networking/volume mounts)
    server_cmd = ["python", "/app/math_server.py"]
    
    logger.info("🔵 CLIENT: Connecting to trusted math-service server")
    
    try:
        async with stdio_client(
            StdioServerParameters(command=server_cmd[0], args=server_cmd[1:])
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List available tools
                tools_response = await session.list_tools()
                logger.info(f"📋 CLIENT: Available tools: {[t.name for t in tools_response.tools]}")
                
                # Use the add tool with sensitive business data
                if any(tool.name == "add" for tool in tools_response.tools):
                    logger.info("🧮 CLIENT: Calling add tool with sensitive financial data")
                    result = await session.call_tool("add", {"a": 42, "b": 13})
                    
                    response_text = [content.text for content in result.content]
                    logger.info(f"📤 CLIENT: Received result: {response_text}")
                    
                    # Save client log (client doesn't know which server actually handled this)
                    os.makedirs("/shared/results", exist_ok=True)
                    with open("/shared/results/client_log.txt", "a") as f:
                        f.write(f"Client received: {response_text}\n")
                
    except Exception as e:
        logger.error(f"❌ CLIENT: Error connecting to math-service: {e}")

if __name__ == "__main__":
    asyncio.run(main())
