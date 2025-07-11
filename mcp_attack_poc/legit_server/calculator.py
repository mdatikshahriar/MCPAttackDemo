import uvicorn
import logging
import math
import statistics
import socket
import json
import inspect
from typing import List, Dict, Any
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_local_ip():
    return "172.18.0.2"

# Initialize FastMCP server
mcp = FastMCP("Scientific Calculator Server")

# MCP JSON-RPC protocol handling
async def handle_mcp_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP JSON-RPC requests"""
    try:
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "Scientific Calculator Server",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }
        
        elif method == "tools/list":
            # Get available tools
            tools = []
            try:
                # Access the tools from FastMCP's tool manager
                tool_manager = mcp._tool_manager
                
                # Get the tools registry from the tool manager
                if hasattr(tool_manager, 'tools'):
                    tools_registry = tool_manager.tools
                elif hasattr(tool_manager, '_tools'):
                    tools_registry = tool_manager._tools
                else:
                    # Fallback: try to find tools in tool_manager attributes
                    tools_registry = None
                    for attr_name in dir(tool_manager):
                        attr_value = getattr(tool_manager, attr_name)
                        if isinstance(attr_value, dict) and attr_value:
                            tools_registry = attr_value
                            break
                
                if tools_registry:
                    for tool_name, function_tool in tools_registry.items():
                        # Extract information from FunctionTool object
                        tool_name = function_tool.name
                        description = function_tool.description or "No description available"
                        
                        # Get the actual function from the FunctionTool
                        if hasattr(function_tool, 'func'):
                            tool_func = function_tool.func
                        elif hasattr(function_tool, 'function'):
                            tool_func = function_tool.function
                        elif hasattr(function_tool, '_func'):
                            tool_func = function_tool._func
                        else:
                            # If we can't find the function, create a basic schema
                            tools.append({
                                "name": tool_name,
                                "description": description,
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            })
                            continue
                        
                        # Get function signature
                        sig = inspect.signature(tool_func)
                        
                        # Build parameter schema
                        parameters = {}
                        for param_name, param in sig.parameters.items():
                            param_type = "string"  # default
                            if param.annotation == float:
                                param_type = "number"
                            elif param.annotation == int:
                                param_type = "integer"
                            elif param.annotation == bool:
                                param_type = "boolean"
                            elif hasattr(param.annotation, '__origin__') and param.annotation.__origin__ is list:
                                param_type = "array"
                            
                            parameters[param_name] = {
                                "type": param_type,
                                "description": f"Parameter {param_name}"
                            }
                        
                        tools.append({
                            "name": tool_name,
                            "description": description,
                            "inputSchema": {
                                "type": "object",
                                "properties": parameters,
                                "required": list(parameters.keys())
                            }
                        })
                else:
                    logger.warning("Could not find tools registry in tool manager")
                    
            except Exception as e:
                logger.error(f"Error getting tools: {e}")
                tools = []
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": tools
                },
                "id": request_id
            }
        
        elif method == "tools/call":
            # Handle tool calls
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                # Use FastMCP's built-in method to call the tool (it's async)
                result = await mcp._call_tool(tool_name, arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result)
                            }
                        ]
                    },
                    "id": request_id
                }
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": f"Tool execution error: {str(e)}"
                    },
                    "id": request_id
                }
        
        elif method == "notifications/initialized":
            # Handle initialization notification (no response needed)
            return None
        
        elif method == "ping":
            # Handle ping request
            return {
                "jsonrpc": "2.0",
                "result": {},
                "id": request_id
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }
    
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": request_data.get("id")
        }

# Add MCP protocol endpoint at root
@mcp.custom_route("/", methods=["POST"])
async def mcp_endpoint(request: Request) -> JSONResponse:
    """MCP protocol endpoint"""
    try:
        # Get the request body
        body = await request.body()
        request_data = json.loads(body.decode('utf-8'))
        
        # Log the incoming request for debugging
        logger.info(f"MCP Request: {request_data}")
        
        # Handle MCP request
        response = await handle_mcp_request(request_data)
        
        # Log the response for debugging
        logger.info(f"MCP Response: {response}")
        
        # Return response if not None (notifications don't need responses)
        if response is not None:
            return JSONResponse(response)
        else:
            return Response(status_code=204)  # No content for notifications
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": "Parse error"
            },
            "id": None
        }, status_code=400)
    except Exception as e:
        logger.error(f"Exception in MCP endpoint: {e}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": None
        }, status_code=500)

# Add health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "service": "scientific-calculator"})

# Add tool discovery endpoint
@mcp.custom_route("/tools", methods=["GET"])
async def list_tools(request: Request) -> JSONResponse:
    """List all available tools"""
    tools = []
    try:
        # Access the tools from FastMCP's tool manager
        tool_manager = mcp._tool_manager
        
        # Get the tools registry from the tool manager
        if hasattr(tool_manager, 'tools'):
            tools_registry = tool_manager.tools
        elif hasattr(tool_manager, '_tools'):
            tools_registry = tool_manager._tools
        else:
            # Fallback: try to find tools in tool_manager attributes
            tools_registry = None
            for attr_name in dir(tool_manager):
                attr_value = getattr(tool_manager, attr_name)
                if isinstance(attr_value, dict) and attr_value:
                    tools_registry = attr_value
                    break
        
        if tools_registry:
            for tool_name, function_tool in tools_registry.items():
                # Extract information from FunctionTool object
                tool_name = function_tool.name
                description = function_tool.description or "No description available"
                
                # Get the actual function from the FunctionTool
                if hasattr(function_tool, 'func'):
                    tool_func = function_tool.func
                elif hasattr(function_tool, 'function'):
                    tool_func = function_tool.function
                elif hasattr(function_tool, '_func'):
                    tool_func = function_tool._func
                else:
                    # If we can't find the function, create a basic schema
                    tools.append({
                        "name": tool_name,
                        "description": description,
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    })
                    continue
                
                # Get function signature
                sig = inspect.signature(tool_func)
                
                # Build parameter schema
                parameters = {}
                for param_name, param in sig.parameters.items():
                    param_type = "string"  # default
                    if param.annotation == float:
                        param_type = "number"
                    elif param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif hasattr(param.annotation, '__origin__') and param.annotation.__origin__ is list:
                        param_type = "array"
                    
                    parameters[param_name] = {
                        "type": param_type,
                        "description": f"Parameter {param_name}"
                    }
                
                tools.append({
                    "name": tool_name,
                    "description": description,
                    "inputSchema": {
                        "type": "object",
                        "properties": parameters,
                        "required": list(parameters.keys())
                    }
                })
        else:
            logger.warning("Could not find tools registry in tool manager")
            
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        tools = []
    
    return JSONResponse({
        "success": True,
        "tools": tools
    })

# Add tool call endpoint
@mcp.custom_route("/call_tool", methods=["POST"])
async def call_tool(request: Request) -> JSONResponse:
    """Call a specific tool with provided arguments"""
    try:
        # Get the request body
        body = await request.body()
        payload = json.loads(body.decode('utf-8'))
        
        # Extract tool name and arguments
        tool_name = payload.get("tool")
        arguments = payload.get("arguments", {})
        
        if not tool_name:
            return JSONResponse({
                "success": False,
                "error": "Tool name is required"
            }, status_code=400)
        
        # Log the tool call for debugging
        logger.info(f"Tool Call: {tool_name} with args: {arguments}")
        
        # Get the tool function directly and call it
        tool_manager = mcp._tool_manager

        # Get the tools registry
        if hasattr(tool_manager, 'tools'):
            tools_registry = tool_manager.tools
        elif hasattr(tool_manager, '_tools'):
            tools_registry = tool_manager._tools
        else:
            raise ValueError("Could not find tools registry")

        if not tools_registry or tool_name not in tools_registry:
            raise ValueError(f"Tool '{tool_name}' not found")

        # Get the actual function from the FunctionTool
        function_tool = tools_registry[tool_name]

        # The function is stored in the 'fn' attribute
        tool_func = function_tool.fn

        # Convert arguments to proper types based on function signature
        sig = inspect.signature(tool_func)
        converted_args = {}
        for param_name, param_value in arguments.items():
            if param_name in sig.parameters:
                param_annotation = sig.parameters[param_name].annotation
                if param_annotation == int and isinstance(param_value, float):
                    converted_args[param_name] = int(param_value)
                elif param_annotation == float and isinstance(param_value, int):
                    converted_args[param_name] = float(param_value)
                else:
                    converted_args[param_name] = param_value
            else:
                converted_args[param_name] = param_value

        # Call the function directly
        result = tool_func(**converted_args)
        
        # Log the result for debugging
        logger.info(f"Tool Result: {result}")
        
        return JSONResponse({
            "success": True,
            "result": result
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JSONResponse({
            "success": False,
            "error": "Invalid JSON payload"
        }, status_code=400)
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# Basic arithmetic operations
@mcp.tool
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

@mcp.tool
def subtract(a: float, b: float) -> float:
    """Subtract two numbers"""
    return a - b

@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

@mcp.tool
def divide(a: float, b: float) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

@mcp.tool
def modulo(a: float, b: float) -> float:
    """Calculate modulo (remainder of division)"""
    if b == 0:
        raise ValueError("Modulo by zero")
    return a % b

@mcp.tool
def abs_value(x: float) -> float:
    """Calculate absolute value"""
    return abs(x)

# Power and root operations
@mcp.tool
def power(a: float, b: float) -> float:
    """Raise a number to a power (a^b)"""
    return a ** b

@mcp.tool
def sqrt(x: float) -> float:
    """Calculate square root"""
    if x < 0:
        raise ValueError("Cannot square root a negative number")
    return math.sqrt(x)

@mcp.tool
def cbrt(x: float) -> float:
    """Calculate cube root"""
    return math.pow(x, 1/3)

@mcp.tool
def nth_root(x: float, n: float) -> float:
    """Calculate nth root of a number"""
    if n == 0:
        raise ValueError("Cannot take 0th root")
    return math.pow(x, 1/n)

# Factorial and combinatorics
@mcp.tool
def factorial(n: int) -> int:
    """Calculate factorial"""
    if n < 0:
        raise ValueError("Factorial of a negative number is not defined")
    return math.factorial(n)

@mcp.tool
def permutation(n: int, r: int) -> int:
    """Calculate permutation P(n,r) = n!/(n-r)!"""
    if n < 0 or r < 0 or r > n:
        raise ValueError("Invalid permutation parameters")
    return math.factorial(n) // math.factorial(n - r)

@mcp.tool
def combination(n: int, r: int) -> int:
    """Calculate combination C(n,r) = n!/(r!(n-r)!)"""
    if n < 0 or r < 0 or r > n:
        raise ValueError("Invalid combination parameters")
    return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))

# Trigonometric functions (radians)
@mcp.tool
def sin(x: float) -> float:
    """Calculate sine (in radians)"""
    return math.sin(x)

@mcp.tool
def cos(x: float) -> float:
    """Calculate cosine (in radians)"""
    return math.cos(x)

@mcp.tool
def tan(x: float) -> float:
    """Calculate tangent (in radians)"""
    return math.tan(x)

@mcp.tool
def asin(x: float) -> float:
    """Calculate arc sine (returns radians)"""
    if x < -1 or x > 1:
        raise ValueError("asin domain error (-1 <= x <= 1)")
    return math.asin(x)

@mcp.tool
def acos(x: float) -> float:
    """Calculate arc cosine (returns radians)"""
    if x < -1 or x > 1:
        raise ValueError("acos domain error (-1 <= x <= 1)")
    return math.acos(x)

@mcp.tool
def atan(x: float) -> float:
    """Calculate arc tangent (returns radians)"""
    return math.atan(x)

@mcp.tool
def atan2(y: float, x: float) -> float:
    """Calculate arc tangent of y/x (returns radians)"""
    return math.atan2(y, x)

# Trigonometric functions (degrees)
@mcp.tool
def sin_deg(x: float) -> float:
    """Calculate sine (in degrees)"""
    return math.sin(math.radians(x))

@mcp.tool
def cos_deg(x: float) -> float:
    """Calculate cosine (in degrees)"""
    return math.cos(math.radians(x))

@mcp.tool
def tan_deg(x: float) -> float:
    """Calculate tangent (in degrees)"""
    return math.tan(math.radians(x))

@mcp.tool
def asin_deg(x: float) -> float:
    """Calculate arc sine (returns degrees)"""
    if x < -1 or x > 1:
        raise ValueError("asin domain error (-1 <= x <= 1)")
    return math.degrees(math.asin(x))

@mcp.tool
def acos_deg(x: float) -> float:
    """Calculate arc cosine (returns degrees)"""
    if x < -1 or x > 1:
        raise ValueError("acos domain error (-1 <= x <= 1)")
    return math.degrees(math.acos(x))

@mcp.tool
def atan_deg(x: float) -> float:
    """Calculate arc tangent (returns degrees)"""
    return math.degrees(math.atan(x))

# Hyperbolic functions
@mcp.tool
def sinh(x: float) -> float:
    """Calculate hyperbolic sine"""
    return math.sinh(x)

@mcp.tool
def cosh(x: float) -> float:
    """Calculate hyperbolic cosine"""
    return math.cosh(x)

@mcp.tool
def tanh(x: float) -> float:
    """Calculate hyperbolic tangent"""
    return math.tanh(x)

@mcp.tool
def asinh(x: float) -> float:
    """Calculate inverse hyperbolic sine"""
    return math.asinh(x)

@mcp.tool
def acosh(x: float) -> float:
    """Calculate inverse hyperbolic cosine"""
    if x < 1:
        raise ValueError("acosh domain error (x >= 1)")
    return math.acosh(x)

@mcp.tool
def atanh(x: float) -> float:
    """Calculate inverse hyperbolic tangent"""
    if x <= -1 or x >= 1:
        raise ValueError("atanh domain error (-1 < x < 1)")
    return math.atanh(x)

# Logarithmic functions
@mcp.tool
def log(x: float) -> float:
    """Calculate natural logarithm"""
    if x <= 0:
        raise ValueError("Logarithm of non-positive number is not defined")
    return math.log(x)

@mcp.tool
def log10(x: float) -> float:
    """Calculate logarithm base 10"""
    if x <= 0:
        raise ValueError("Logarithm of non-positive number is not defined")
    return math.log10(x)

@mcp.tool
def log2(x: float) -> float:
    """Calculate logarithm base 2"""
    if x <= 0:
        raise ValueError("Logarithm of non-positive number is not defined")
    return math.log2(x)

@mcp.tool
def log_base(x: float, base: float) -> float:
    """Calculate logarithm with custom base"""
    if x <= 0 or base <= 0 or base == 1:
        raise ValueError("Invalid logarithm parameters")
    return math.log(x) / math.log(base)

@mcp.tool
def exp(x: float) -> float:
    """Calculate e^x"""
    return math.exp(x)

@mcp.tool
def exp2(x: float) -> float:
    """Calculate 2^x"""
    return math.pow(2, x)

# Rounding and ceiling functions
@mcp.tool
def floor(x: float) -> int:
    """Calculate floor (largest integer <= x)"""
    return math.floor(x)

@mcp.tool
def ceil(x: float) -> int:
    """Calculate ceiling (smallest integer >= x)"""
    return math.ceil(x)

@mcp.tool
def round_number(x: float, decimals: int = 0) -> float:
    """Round to nearest integer or specified decimal places"""
    return round(x, decimals)

@mcp.tool
def trunc(x: float) -> int:
    """Truncate to integer part"""
    return math.trunc(x)

# Angle conversion
@mcp.tool
def deg_to_rad(degrees: float) -> float:
    """Convert degrees to radians"""
    return math.radians(degrees)

@mcp.tool
def rad_to_deg(radians: float) -> float:
    """Convert radians to degrees"""
    return math.degrees(radians)

# Statistical functions
@mcp.tool
def mean(numbers: List[float]) -> float:
    """Calculate mean of a list"""
    return statistics.mean(numbers)

@mcp.tool
def median(numbers: List[float]) -> float:
    """Calculate median of a list"""
    return statistics.median(numbers)

@mcp.tool
def mode(numbers: List[float]) -> float:
    """Calculate mode of a list"""
    try:
        return statistics.mode(numbers)
    except statistics.StatisticsError:
        raise ValueError("No unique mode found")

@mcp.tool
def stdev(numbers: List[float]) -> float:
    """Calculate standard deviation"""
    if len(numbers) < 2:
        raise ValueError("Standard deviation requires at least 2 numbers")
    return statistics.stdev(numbers)

@mcp.tool
def variance(numbers: List[float]) -> float:
    """Calculate variance"""
    if len(numbers) < 2:
        raise ValueError("Variance requires at least 2 numbers")
    return statistics.variance(numbers)

@mcp.tool
def range_calc(numbers: List[float]) -> float:
    """Calculate range (max - min)"""
    if len(numbers) == 0:
        raise ValueError("Range requires at least 1 number")
    return max(numbers) - min(numbers)

@mcp.tool
def sum_list(numbers: List[float]) -> float:
    """Calculate sum of a list"""
    return sum(numbers)

@mcp.tool
def product(numbers: List[float]) -> float:
    """Calculate product of a list"""
    result = 1
    for num in numbers:
        result *= num
    return result

@mcp.tool
def min_value(numbers: List[float]) -> float:
    """Find minimum value in a list"""
    if len(numbers) == 0:
        raise ValueError("Min requires at least 1 number")
    return min(numbers)

@mcp.tool
def max_value(numbers: List[float]) -> float:
    """Find maximum value in a list"""
    if len(numbers) == 0:
        raise ValueError("Max requires at least 1 number")
    return max(numbers)

# Constants
@mcp.tool
def pi() -> float:
    """Get the value of π"""
    return math.pi

@mcp.tool
def e() -> float:
    """Get the value of e"""
    return math.e

@mcp.tool
def tau() -> float:
    """Get the value of τ (2π)"""
    return math.tau

@mcp.tool
def golden_ratio() -> float:
    """Get the golden ratio φ"""
    return (1 + math.sqrt(5)) / 2

# Number theory
@mcp.tool
def gcd(a: int, b: int) -> int:
    """Calculate greatest common divisor"""
    return math.gcd(a, b)

@mcp.tool
def lcm(a: int, b: int) -> int:
    """Calculate least common multiple"""
    if a == 0 and b == 0:
        return 0
    return abs(a * b) // math.gcd(a, b)

@mcp.tool
def is_prime(n: int) -> bool:
    """Check if a number is prime"""
    if n < 2:
        return False
    elif n == 2:
        return True
    elif n % 2 == 0:
        return False
    else:
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True

def main():
    """Main function to start the MCP server"""
    # Get local IP address
    local_ip = get_local_ip()
    
    logger.info(f"🟢 SCIENTIFIC CALCULATOR MCP: Starting server on {local_ip}:5234")
    
    # Run the FastMCP server as HTTP server
    uvicorn.run(mcp.http_app, host=local_ip, port=5234)

if __name__ == "__main__":
    main()
