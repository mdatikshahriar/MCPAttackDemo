import streamlit as st
from openai import OpenAI
import asyncio
import logging
import os
import re
from typing import Dict, Any, List, Optional, Tuple
import aiohttp
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- MCP Client Class ---
class MCPClient:
    def __init__(self, server_url: str = None):
        self.server_url = server_url or os.getenv("MCP_SERVER_URL", "http://math-calculator.local:5234")
        self.available_tools = []
        self.server_status = "Unknown"
        self.last_health_check = 0
        
    async def check_server_health(self) -> Dict[str, Any]:
        """Check if the MCP server is healthy and responsive."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.server_status = "Healthy"
                        self.last_health_check = time.time()
                        logger.info(f"✅ MCP Server health check passed: {result}")
                        return {"success": True, "status": result}
                    else:
                        self.server_status = "Unhealthy"
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            self.server_status = "Unreachable"
            logger.error(f"❌ Health check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def fetch_available_tools(self) -> Dict[str, Any]:
        """Fetch the list of available tools from the MCP server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/tools",
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            self.available_tools = result.get("tools", [])
                            logger.info(f"📊 Fetched {len(self.available_tools)} tools from server")
                            return {"success": True, "tools": self.available_tools}
                        else:
                            return {"success": False, "error": result.get("error", "Unknown error")}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"❌ Failed to fetch tools: {e}")
            return {"success": False, "error": str(e)}
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP server."""
        try:
            payload = {
                "tool": tool_name,
                "params": params
            }
            
            logger.info(f"🧮 Calling tool '{tool_name}' with params: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/call_tool",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            return {"success": True, "result": result.get("result", "No result returned")}
                        else:
                            return {"success": False, "error": result.get("error", "Unknown error")}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"❌ Tool call failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def initialize(self) -> bool:
        """Initialize the MCP client by checking health and fetching tools."""
        # Check server health
        health_result = await self.check_server_health()
        if not health_result["success"]:
            logger.error(f"❌ Server health check failed: {health_result['error']}")
            return False
        
        # Fetch available tools
        tools_result = await self.fetch_available_tools()
        if not tools_result["success"]:
            logger.error(f"❌ Failed to fetch tools: {tools_result['error']}")
            return False
        
        logger.info(f"✅ MCP Client initialized successfully with {len(self.available_tools)} tools")
        return True
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Dict]:
        """Get tool details by name."""
        for tool in self.available_tools:
            if tool.get("name") == tool_name:
                return tool
        return None
    
    def get_tools_by_category(self) -> Dict[str, List[Dict]]:
        """Organize tools by category based on their descriptions."""
        categories = {
            "Basic Arithmetic": [],
            "Trigonometry": [],
            "Logarithms": [],
            "Statistics": [],
            "Constants": [],
            "Other": []
        }
        
        for tool in self.available_tools:
            name = tool.get("name", "")
            desc = tool.get("description", "").lower()
            
            if any(word in desc for word in ["add", "subtract", "multiply", "divide", "power", "root", "factorial"]):
                categories["Basic Arithmetic"].append(tool)
            elif any(word in desc for word in ["sin", "cos", "tan", "hyperbolic"]):
                categories["Trigonometry"].append(tool)
            elif any(word in desc for word in ["log", "exp", "logarithm"]):
                categories["Logarithms"].append(tool)
            elif any(word in desc for word in ["mean", "median", "standard", "variance", "sum", "min", "max"]):
                categories["Statistics"].append(tool)
            elif any(word in desc for word in ["pi", "value of"]):
                categories["Constants"].append(tool)
            else:
                categories["Other"].append(tool)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}


# --- Helper Functions ---
def extract_numbers_from_query(query: str) -> List[float]:
    """Extract all numbers from a query string."""
    number_pattern = r'-?\d+\.?\d*(?:[eE][+-]?\d+)?'
    numbers = re.findall(number_pattern, query)
    try:
        return [float(n) for n in numbers]
    except ValueError:
        return []

def extract_arrays_from_query(query: str) -> List[List[float]]:
    """Extract arrays from query string (e.g., [1, 2, 3])."""
    array_pattern = r'\[([^\]]+)\]'
    arrays = re.findall(array_pattern, query)
    result = []
    for arr_str in arrays:
        try:
            numbers = [float(n.strip()) for n in arr_str.split(',')]
            result.append(numbers)
        except ValueError:
            continue
    return result

def detect_math_tool_and_extract_args(query: str, available_tools: List[Dict]) -> Optional[Tuple[str, Dict]]:
    """
    Detects which math tool to use based on the query and available tools.
    Returns (tool_name, params) or None if no math operation is detected.
    """
    query_lower = query.lower()
    numbers = extract_numbers_from_query(query)
    arrays = extract_arrays_from_query(query)
    
    # Enhanced tool patterns with comprehensive coverage
    tool_patterns = [
        # Basic arithmetic operations
        (r'\badd\b|\bplus\b|\+(?!\+)', 'two_nums', 'add', ['a', 'b']),
        (r'\bsubtract\b|\bminus\b|\-(?!\-)(?!\d)', 'two_nums', 'subtract', ['a', 'b']),
        (r'\bmultiply\b|\btimes\b|\*(?!\*)', 'two_nums', 'multiply', ['a', 'b']),
        (r'\bdivide\b|\bdivision\b|\/(?!\/)', 'two_nums', 'divide', ['a', 'b']),
        (r'\bmodulo\b|\bmod\b|\bremainder\b|%', 'two_nums', 'modulo', ['a', 'b']),
        (r'\babsolute\b|\babs\b', 'one_num', 'abs', ['x']),
        
        # Power and root operations
        (r'\bpower\b|\bexponent\b|\braise.*power\b|\^|\*\*', 'two_nums', 'power', ['a', 'b']),
        (r'\bsquare root\b|\bsqrt\b|√', 'one_num', 'sqrt', ['x']),
        (r'\bcube root\b|\bcbrt\b|∛', 'one_num', 'cbrt', ['x']),
        (r'\bnth root\b|\broot\b.*\bof\b', 'two_nums', 'nth_root', ['x', 'n']),
        
        # Factorial and combinatorics
        (r'\bfactorial\b|!', 'one_num', 'factorial', ['n']),
        (r'\bpermutation\b|\bperm\b|\bP\(', 'two_nums', 'permutation', ['n', 'r']),
        (r'\bcombination\b|\bcomb\b|\bC\(|\bchoose\b', 'two_nums', 'combination', ['n', 'r']),
        
        # Trigonometric functions (radians)
        (r'\bsin\b(?!\w)', 'one_num', 'sin', ['x']),
        (r'\bcos\b(?!\w)', 'one_num', 'cos', ['x']),
        (r'\btan\b(?!\w)', 'one_num', 'tan', ['x']),
        (r'\basin\b|\barcsine\b|\barcsin\b|\bsin\^-1\b', 'one_num', 'asin', ['x']),
        (r'\bacos\b|\barccosine\b|\barccos\b|\bcos\^-1\b', 'one_num', 'acos', ['x']),
        (r'\batan\b|\barctangent\b|\barctan\b|\btan\^-1\b', 'one_num', 'atan', ['x']),
        (r'\batan2\b', 'two_nums', 'atan2', ['y', 'x']),
        
        # Trigonometric functions (degrees)
        (r'\bsin.*degree\b|\bsind\b', 'one_num', 'sin_deg', ['x']),
        (r'\bcos.*degree\b|\bcosd\b', 'one_num', 'cos_deg', ['x']),
        (r'\btan.*degree\b|\btand\b', 'one_num', 'tan_deg', ['x']),
        (r'\basin.*degree\b|\basind\b', 'one_num', 'asin_deg', ['x']),
        (r'\bacos.*degree\b|\bacosd\b', 'one_num', 'acos_deg', ['x']),
        (r'\batan.*degree\b|\batand\b', 'one_num', 'atan_deg', ['x']),
        
        # Hyperbolic functions
        (r'\bsinh\b|\bhyperbolic sine\b', 'one_num', 'sinh', ['x']),
        (r'\bcosh\b|\bhyperbolic cosine\b', 'one_num', 'cosh', ['x']),
        (r'\btanh\b|\bhyperbolic tangent\b', 'one_num', 'tanh', ['x']),
        (r'\basinh\b|\binverse hyperbolic sine\b', 'one_num', 'asinh', ['x']),
        (r'\bacosh\b|\binverse hyperbolic cosine\b', 'one_num', 'acosh', ['x']),
        (r'\batanh\b|\binverse hyperbolic tangent\b', 'one_num', 'atanh', ['x']),
        
        # Logarithmic functions
        (r'\bnatural log\b|\bln\b|\blog\b(?!\d)', 'one_num', 'log', ['x']),
        (r'\blog base 10\b|\blog10\b|\blg\b', 'one_num', 'log10', ['x']),
        (r'\blog base 2\b|\blog2\b|\blb\b', 'one_num', 'log2', ['x']),
        (r'\blog base\b|\blogarithm base\b', 'two_nums', 'log_base', ['x', 'base']),
        (r'\bexp\b|\be\^|\bexponential\b', 'one_num', 'exp', ['x']),
        (r'\bexp2\b|\b2\^', 'one_num', 'exp2', ['x']),
        
        # Rounding and ceiling functions
        (r'\bfloor\b|⌊', 'one_num', 'floor', ['x']),
        (r'\bceiling\b|\bceil\b|⌈', 'one_num', 'ceil', ['x']),
        (r'\bround\b|\brounding\b', 'one_num_optional', 'round', ['x', 'decimals']),
        (r'\btruncate\b|\btrunc\b', 'one_num', 'trunc', ['x']),
        
        # Angle conversion
        (r'\bdegrees to radians\b|\bdeg to rad\b', 'one_num', 'deg_to_rad', ['degrees']),
        (r'\bradians to degrees\b|\brad to deg\b', 'one_num', 'rad_to_deg', ['radians']),
        
        # Statistical functions
        (r'\bmean\b|\baverage\b', 'array', 'mean', ['numbers']),
        (r'\bmedian\b', 'array', 'median', ['numbers']),
        (r'\bmode\b', 'array', 'mode', ['numbers']),
        (r'\bstandard deviation\b|\bstdev\b|\bstd\b', 'array', 'stdev', ['numbers']),
        (r'\bvariance\b|\bvar\b', 'array', 'variance', ['numbers']),
        (r'\brange\b', 'array', 'range', ['numbers']),
        (r'\bsum\b|\btotal\b', 'array', 'sum', ['numbers']),
        (r'\bproduct\b|\bmultiply all\b', 'array', 'product', ['numbers']),
        (r'\bminimum\b|\bmin\b', 'array', 'min', ['numbers']),
        (r'\bmaximum\b|\bmax\b', 'array', 'max', ['numbers']),
        
        # Constants
        (r'\bpi\b|π', 'no_args', 'pi', []),
        (r'\beuler\b|\be\b(?!\w)', 'no_args', 'e', []),
        (r'\btau\b|τ', 'no_args', 'tau', []),
        (r'\bgolden ratio\b|\bgolden\b|\bphi\b|φ', 'no_args', 'golden_ratio', []),
        
        # Number theory
        (r'\bgcd\b|\bgreatest common divisor\b', 'two_nums', 'gcd', ['a', 'b']),
        (r'\blcm\b|\bleast common multiple\b', 'two_nums', 'lcm', ['a', 'b']),
        (r'\bis prime\b|\bprime\b.*\bcheck\b', 'one_num', 'is_prime', ['n']),
    ]

    # Create a set of available tool names for quick lookup
    available_tool_names = {tool.get("name") for tool in available_tools}

    # Try to match patterns and extract arguments
    for pattern, arg_type, tool_name, arg_names in tool_patterns:
        if re.search(pattern, query_lower) and tool_name in available_tool_names:
            try:
                # Handle different argument types
                if arg_type == 'two_nums' and len(numbers) >= 2:
                    return tool_name, {arg_names[0]: numbers[0], arg_names[1]: numbers[1]}
                elif arg_type == 'one_num' and len(numbers) >= 1:
                    return tool_name, {arg_names[0]: numbers[0]}
                elif arg_type == 'one_num_optional' and len(numbers) >= 1:
                    params = {arg_names[0]: numbers[0]}
                    if len(numbers) >= 2:
                        params[arg_names[1]] = numbers[1]
                    return tool_name, params
                elif arg_type == 'array':
                    # First try to use explicitly defined arrays [1,2,3]
                    if arrays:
                        return tool_name, {arg_names[0]: arrays[0]}
                    # Otherwise use all numbers as an array
                    elif len(numbers) > 1:
                        return tool_name, {arg_names[0]: numbers}
                elif arg_type == 'no_args':
                    return tool_name, {}
            except (ValueError, IndexError) as e:
                logger.warning(f"Arg extraction failed for '{tool_name}': {e}")
                continue
    
    return None

def is_math_query(query: str) -> bool:
    """Determines if a query is likely a math calculation request."""
    if not query or not query.strip():
        return False
        
    query_lower = query.lower()
    
    # Mathematical keywords that strongly indicate math operations
    strong_math_keywords = [
        'calculate', 'compute', 'solve', 'find', 'what is', 'what\'s',
        'add', 'subtract', 'multiply', 'divide', 'power', 'sqrt', 'root',
        'sin', 'cos', 'tan', 'log', 'exp', 'factorial', 'mean', 'median',
        'mode', 'variance', 'deviation', 'sum', 'product', 'minimum', 'maximum',
        'floor', 'ceil', 'round', 'absolute', 'prime', 'gcd', 'lcm'
    ]
    
    # Mathematical symbols that indicate calculations
    math_symbols = ['+', '-', '*', '/', '^', '√', 'π', '∛', '%', '!']
    
    # Mathematical expressions patterns
    math_expression_patterns = [
        r'\d+\s*[+\-*/^%]\s*\d+',  # Simple expressions like "5 + 3"
        r'\d+\s*\^\s*\d+',          # Power expressions like "2^3"
        r'\d+\s*!\s*',              # Factorial like "5!"
        r'\[\s*\d+(?:\s*,\s*\d+)*\s*\]',  # Arrays like [1,2,3]
    ]
    
    # Check for strong math keywords
    for keyword in strong_math_keywords:
        if keyword in query_lower:
            return True
    
    # Check for math symbols
    for symbol in math_symbols:
        if symbol in query:
            return True
    
    # Check for mathematical expression patterns
    for pattern in math_expression_patterns:
        if re.search(pattern, query):
            return True
    
    return False

def format_math_response(tool_name: str, result: str, params: Dict) -> str:
    """Formats the mathematical result in a user-friendly way."""
    try:
        # Clean the result string
        result = str(result).strip()
        
        # Try to parse as a number for better formatting
        if result.replace('.', '').replace('-', '').replace('e', '').replace('+', '').replace('E', '').isdigit() or result.replace('.', '').replace('-', '').isdigit():
            try:
                num_result = float(result)
                
                # Format very large or very small numbers
                if abs(num_result) >= 1e6 or (abs(num_result) < 1e-3 and num_result != 0):
                    formatted_result = f"{num_result:.6e}"
                else:
                    # Format with appropriate decimal places
                    if num_result == int(num_result):
                        formatted_result = str(int(num_result))
                    else:
                        formatted_result = f"{num_result:.10f}".rstrip('0').rstrip('.')
            except ValueError:
                formatted_result = result
        else:
            formatted_result = result
        
        # Create a descriptive response
        operation_descriptions = {
            'add': f"Adding {params.get('a')} + {params.get('b')}",
            'subtract': f"Subtracting {params.get('a')} - {params.get('b')}",
            'multiply': f"Multiplying {params.get('a')} × {params.get('b')}",
            'divide': f"Dividing {params.get('a')} ÷ {params.get('b')}",
            'power': f"Calculating {params.get('a')}^{params.get('b')}",
            'sqrt': f"Square root of {params.get('x')}",
            'factorial': f"Factorial of {params.get('n')}",
            'mean': f"Mean of {params.get('numbers')}",
            'pi': "Value of π",
            'e': "Value of e",
        }
        
        description = operation_descriptions.get(tool_name, f"Result of {tool_name}")
        
        return f"**{description}** = **{formatted_result}**"
        
    except Exception as e:
        logger.error(f"Error formatting math response: {e}")
        return f"**Result:** {result}"

def get_openai_client():
    """Initialize OpenAI client with error handling."""
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        return None, "OpenRouter API key not found in environment variables."
    
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
            default_headers={
                "HTTP-Referer": os.getenv("RENDER_URL", "http://localhost:8501"), 
                "X-Title": "MCP Scientific Calculator Chatbot",
            },
        )
        return client, None
    except Exception as e:
        return None, f"Error initializing OpenAI client: {str(e)}"

def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="MCP Scientific Calculator", page_icon="🧮")
    st.title("🧮 MCP Scientific Calculator Chatbot")

    # Initialize MCP client
    if "mcp_client" not in st.session_state:
        st.session_state.mcp_client = MCPClient()
        st.session_state.mcp_initialized = False
    
    # Initialize OpenAI client
    openai_client, error = get_openai_client()
    if error:
        st.error(f"Configuration Error: {error}")
        st.info("Please set the `OPENROUTER_API_KEY` environment variable.")
        st.stop()

    # Server status in sidebar
    with st.sidebar:
        st.header("🔌 Server Status")
        
        if st.button("🔄 Refresh Server Status"):
            with st.spinner("Checking server health..."):
                health_result = asyncio.run(st.session_state.mcp_client.check_server_health())
                if health_result["success"]:
                    st.success("✅ Server is healthy!")
                else:
                    st.error(f"❌ Server issue: {health_result['error']}")
        
        # Display current server status
        status_color = {"Healthy": "🟢", "Unhealthy": "🟡", "Unreachable": "🔴"}.get(st.session_state.mcp_client.server_status, "⚪")
        st.write(f"Status: {status_color} {st.session_state.mcp_client.server_status}")
        st.write(f"Server URL: `{st.session_state.mcp_client.server_url}`")
        
        # Initialize MCP client if not done
        if not st.session_state.mcp_initialized:
            with st.spinner("Initializing MCP client..."):
                success = asyncio.run(st.session_state.mcp_client.initialize())
                if success:
                    st.session_state.mcp_initialized = True
                    st.success("✅ MCP Client initialized!")
                else:
                    st.error("❌ Failed to initialize MCP client")
        
        # Display available tools organized by category
        if st.session_state.mcp_initialized and st.session_state.mcp_client.available_tools:
            st.header("🛠️ Available Tools")
            
            # Button to refresh tools
            if st.button("🔄 Refresh Tools"):
                with st.spinner("Fetching tools..."):
                    tools_result = asyncio.run(st.session_state.mcp_client.fetch_available_tools())
                    if tools_result["success"]:
                        st.success(f"✅ Loaded {len(st.session_state.mcp_client.available_tools)} tools")
                    else:
                        st.error(f"❌ Failed to load tools: {tools_result['error']}")
            
            # Display tools by category
            categories = st.session_state.mcp_client.get_tools_by_category()
            for category, tools in categories.items():
                with st.expander(f"{category} ({len(tools)} tools)"):
                    for tool in tools:
                        st.markdown(f"**{tool['name']}**: {tool['description']}")
        
        # Display total tool count
        tool_count = len(st.session_state.mcp_client.available_tools)
        st.metric("Total Tools", tool_count)

    # Main chat interface
    if not st.session_state.mcp_initialized:
        st.warning("⚠️ MCP client not initialized. Please check the server connection.")
        st.stop()

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if prompt := st.chat_input("Ask a question or perform a calculation..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            response = ""
            
            # Determine if this is a math query
            if is_math_query(prompt):
                # Try to extract math tool and parameters
                math_task = detect_math_tool_and_extract_args(prompt, st.session_state.mcp_client.available_tools)
                
                if math_task:
                    tool_name, params = math_task
                    with st.spinner(f"Calculating using **{tool_name}**..."):
                        try:
                            result = asyncio.run(st.session_state.mcp_client.call_tool(tool_name, params))
                            if result["success"]:
                                response = format_math_response(tool_name, result["result"], params)
                            else:
                                response = f"❌ Error performing calculation: {result['error']}"
                        except Exception as e:
                            logger.error(f"Error in MCP calculation: {e}")
                            response = f"❌ Error performing calculation: {str(e)}"
                else:
                    # Math query but couldn't extract specific tool - let AI handle it
                    with st.spinner("Processing mathematical query..."):
                        try:
                            completion = openai_client.chat.completions.create(
                                model="deepseek/deepseek-r1-0528:free",
                                messages=[
                                    {"role": "system", "content": "You are a helpful mathematical assistant. If the user asks for calculations, try to provide step-by-step solutions. For complex calculations, suggest using specific mathematical functions."},
                                    *st.session_state.messages
                                ],
                                max_tokens=1000,
                                temperature=0.7
                            )
                            response = completion.choices[0].message.content
                        except Exception as e:
                            logger.error(f"Error in AI completion: {e}")
                            response = f"❌ Sorry, an error occurred: {str(e)}"
            else:
                # Regular conversation - use AI model
                with st.spinner("Thinking..."):
                    try:
                        completion = openai_client.chat.completions.create(
                            model="mistralai/mistral-7b-instruct:free",
                            messages=[
                                {"role": "system", "content": "You are a helpful and friendly assistant. You have access to a scientific calculator for mathematical operations, but this query doesn't seem to require calculations."},
                                *st.session_state.messages
                            ],
                            max_tokens=1000,
                            temperature=0.7
                        )
                        response = completion.choices[0].message.content
                    except Exception as e:
                        logger.error(f"Error in AI completion: {e}")
                        response = f"❌ Sorry, an error occurred with the AI model: {str(e)}"
            
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Add example queries
    with st.expander("Example Queries"):
        st.markdown("""
        **Basic Math:**
        - "What is 15 + 27?"
        - "Calculate 2 to the power of 8"
        - "Find the square root of 144"
        
        **Trigonometry:**
        - "What is sin of 30 degrees?"
        - "Calculate cos of π/4"
        - "Find arctan of 1"
        
        **Statistics:**
        - "Calculate the mean of [1, 2, 3, 4, 5]"
        - "Find the standard deviation of 10, 20, 30, 40, 50"
        - "What is the median of [7, 2, 9, 1, 5]?"
        
        **Advanced:**
        - "Calculate 10!"
        - "Find the combination of 10 choose 3"
        - "What is the natural log of 100?"
        - "Is 97 prime?"
        """)

if __name__ == "__main__":
    main()
