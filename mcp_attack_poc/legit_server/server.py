import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("math-service")

@server.list_tools()
async def list_tools():
    logger.info("📊 LEGITIMATE SERVER: Listing tools")
    return [
        Tool(
            name="add",
            description="Add two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name, args):
    logger.info(f"✅ LEGITIMATE SERVER: Processing {name} with args: {args}")
    if name == "add":
        result = float(args['a']) + float(args['b'])
        return [TextContent(type="text", text=f"[LEGIT] Sum: {result}")]
    return [TextContent(type="text", text="Unknown tool")]

async def main():
    logger.info("🟢 LEGITIMATE SERVER: Starting...")
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
