import asyncio
import logging
import math
import statistics
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("scientific-calculator")

@server.list_tools()
async def list_tools():
    logger.info("📊 SCIENTIFIC CALCULATOR: Listing all tools")
    return [
        Tool(name="add", description="Add two numbers", inputSchema={"type":"object", "properties":{"a":{"type":"number"}, "b":{"type":"number"}},"required":["a","b"]}),
        Tool(name="subtract", description="Subtract two numbers", inputSchema={"type":"object", "properties":{"a":{"type":"number"}, "b":{"type":"number"}},"required":["a","b"]}),
        Tool(name="multiply", description="Multiply two numbers", inputSchema={"type":"object", "properties":{"a":{"type":"number"}, "b":{"type":"number"}},"required":["a","b"]}),
        Tool(name="divide", description="Divide two numbers", inputSchema={"type":"object", "properties":{"a":{"type":"number"}, "b":{"type":"number"}},"required":["a","b"]}),
        Tool(name="power", description="Raise a number to a power (a^b)", inputSchema={"type":"object", "properties":{"a":{"type":"number"}, "b":{"type":"number"}},"required":["a","b"]}),
        Tool(name="sqrt", description="Calculate square root", inputSchema={"type":"object", "properties":{"x":{"type":"number"}},"required":["x"]}),
        Tool(name="factorial", description="Calculate factorial", inputSchema={"type":"object", "properties":{"n":{"type":"number"}},"required":["n"]}),
        Tool(name="sin", description="Calculate sine (in radians)", inputSchema={"type":"object", "properties":{"x":{"type":"number"}},"required":["x"]}),
        Tool(name="cos", description="Calculate cosine (in radians)", inputSchema={"type":"object", "properties":{"x":{"type":"number"}},"required":["x"]}),
        Tool(name="tan", description="Calculate tangent (in radians)", inputSchema={"type":"object", "properties":{"x":{"type":"number"}},"required":["x"]}),
        Tool(name="log", description="Calculate natural logarithm", inputSchema={"type":"object", "properties":{"x":{"type":"number"}},"required":["x"]}),
        Tool(name="log10", description="Calculate logarithm base 10", inputSchema={"type":"object", "properties":{"x":{"type":"number"}},"required":["x"]}),
        Tool(name="mean", description="Calculate mean of a list", inputSchema={"type":"object", "properties":{"numbers":{"type":"array", "items":{"type":"number"}}},"required":["numbers"]}),
        Tool(name="median", description="Calculate median of a list", inputSchema={"type":"object", "properties":{"numbers":{"type":"array", "items":{"type":"number"}}},"required":["numbers"]}),
        Tool(name="mode", description="Calculate mode of a list", inputSchema={"type":"object", "properties":{"numbers":{"type":"array", "items":{"type":"number"}}},"required":["numbers"]}),
        Tool(name="stdev", description="Calculate standard deviation", inputSchema={"type":"object", "properties":{"numbers":{"type":"array", "items":{"type":"number"}}},"required":["numbers"]}),
        Tool(name="variance", description="Calculate variance", inputSchema={"type":"object", "properties":{"numbers":{"type":"array", "items":{"type":"number"}}},"required":["numbers"]}),
        Tool(name="pi", description="Get the value of π", inputSchema={"type":"object", "properties":{},"required":[]}),
        Tool(name="e", description="Get the value of e", inputSchema={"type":"object", "properties":{},"required":[]}),
    ]

@server.call_tool()
async def call_tool(name, args):
    logger.info(f"🧮 SCIENTIFIC CALCULATOR: Processing {name} with args: {args}")
    try:
        result = None
        if name == "add": result = float(args['a']) + float(args['b'])
        elif name == "subtract": result = float(args['a']) - float(args['b'])
        elif name == "multiply": result = float(args['a']) * float(args['b'])
        elif name == "divide":
            if float(args['b']) == 0: return [TextContent(type="text", text="Error: Division by zero")]
            result = float(args['a']) / float(args['b'])
        elif name == "power": result = float(args['a']) ** float(args['b'])
        elif name == "sqrt":
            if float(args['x']) < 0: return [TextContent(type="text", text="Error: Cannot square root a negative number.")]
            result = math.sqrt(float(args['x']))
        elif name == "factorial":
            if int(args['n']) < 0: return [TextContent(type="text", text="Error: Factorial of a negative number is not defined.")]
            result = math.factorial(int(args['n']))
        elif name == "sin": result = math.sin(float(args['x']))
        elif name == "cos": result = math.cos(float(args['x']))
        elif name == "tan": result = math.tan(float(args['x']))
        elif name == "log":
            if float(args['x']) <= 0: return [TextContent(type="text", text="Error: Logarithm of non-positive number is not defined.")]
            result = math.log(float(args['x']))
        elif name == "log10":
            if float(args['x']) <= 0: return [TextContent(type="text", text="Error: Logarithm of non-positive number is not defined.")]
            result = math.log10(float(args['x']))
        elif name == "mean": result = statistics.mean(args['numbers'])
        elif name == "median": result = statistics.median(args['numbers'])
        elif name == "mode":
            try: result = statistics.mode(args['numbers'])
            except statistics.StatisticsError: return [TextContent(type="text", text="Error: No unique mode found.")]
        elif name == "stdev":
            if len(args['numbers']) < 2: return [TextContent(type="text", text="Error: Standard deviation requires at least 2 numbers.")]
            result = statistics.stdev(args['numbers'])
        elif name == "variance":
            if len(args['numbers']) < 2: return [TextContent(type="text", text="Error: Variance requires at least 2 numbers.")]
            result = statistics.variance(args['numbers'])
        elif name == "pi": result = math.pi
        elif name == "e": result = math.e
        else: return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"Error in {name}: {str(e)}")
        return [TextContent(type="text", text=f"An error occurred: {str(e)}")]

async def main():
    logger.info("🟢 SCIENTIFIC CALCULATOR: Starting...")
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
