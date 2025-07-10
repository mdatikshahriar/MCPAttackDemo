import streamlit as st
from openai import OpenAI
import asyncio
import logging
import os
import re
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from typing import Dict, Any, List, Optional, Tuple

# --- MCP Client Setup ---
async def call_mcp_tool(tool_name: str, params: Dict[str, Any]) -> str:
    """Connects to the MCP server and calls a specific tool with given parameters."""
    # Configure logging *inside* the function to ensure it's always in scope
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    server_cmd = ["python", "/app/math_server.py"]
    try:
        async with stdio_client(
            StdioServerParameters(command=server_cmd[0], args=server_cmd[1:])
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                logger.info(f"Calling MCP tool '{tool_name}' with params: {params}")
                result = await session.call_tool(tool_name, params)
                response_text = [content.text for content in result.content]
                return response_text[0] if response_text else "Error: Empty response from server."
    except Exception as e:
        logger.error(f"Error calling MCP tool '{tool_name}': {e}")
        return f"Error connecting to calculator for tool '{tool_name}'."


def detect_math_tool_and_extract_args(query: str) -> Optional[Tuple[str, Dict]]:
    """
    Detects which math tool to use based on the query and extracts the arguments.
    """
    # This function remains the same as the previous version.
    # For brevity, it is not repeated here.
    query_lower = query.lower()
    
    # Fully synchronized tool patterns
    tool_patterns = [
        (r"add|plus|\+", 'two_nums', 'add', ['a', 'b']),
        (r"subtract|minus|-", 'two_nums', 'subtract', ['a', 'b']),
        (r"multiply|times|\*", 'two_nums', 'multiply', ['a', 'b']),
        (r"divide|/", 'two_nums', 'divide', ['a', 'b']),
        (r"power|exponent|\^", 'two_nums', 'power', ['a', 'b']),
        (r"square root|sqrt", 'one_num', 'sqrt', ['x']),
        (r"factorial", 'one_num', 'factorial', ['n']),
        (r"sin", 'one_num', 'sin', ['x']),
        (r"cos", 'one_num', 'cos', ['x']),
        (r"tan", 'one_num', 'tan', ['x']),
        (r"natural log|ln|log(?!\d)", 'one_num', 'log', ['x']),
        (r"log base 10|log10", 'one_num', 'log10', ['x']),
        (r"mean|average", 'array', 'mean', ['numbers']),
        (r"median", 'array', 'median', ['numbers']),
        (r"mode", 'array', 'mode', ['numbers']),
        (r"standard deviation|stdev", 'array', 'stdev', ['numbers']),
        (r"variance", 'array', 'variance', ['numbers']),
        (r"pi|π", 'no_args', 'pi', []),
        (r"euler|e", 'no_args', 'e', []),
    ]

    for pattern, arg_type, tool_name, arg_names in tool_patterns:
        if re.search(pattern, query_lower):
            try:
                numbers = [float(n) for n in re.findall(r"-?\d+\.?\d*", query)]
                arrays = [
                    [float(n.strip()) for n in arr.split(',')]
                    for arr in re.findall(r"\[([^\]]+)\]", query)
                ]

                if arg_type == 'two_nums' and len(numbers) >= 2:
                    return tool_name, {arg_names[0]: numbers[0], arg_names[1]: numbers[1]}
                if arg_type == 'one_num' and len(numbers) >= 1:
                    return tool_name, {arg_names[0]: numbers[0]}
                if arg_type == 'array' and arrays:
                    return tool_name, {arg_names[0]: arrays[0]}
                if arg_type == 'array' and len(numbers) > 1:
                    return tool_name, {arg_names[0]: numbers}
                if arg_type == 'no_args':
                    return tool_name, {}
            except (ValueError, IndexError) as e:
                # Using a local logger for this function, or just print for simplicity
                print(f"Arg extraction failed for '{tool_name}': {e}")
                continue
    return None

# --- OpenRouter and Streamlit Setup ---

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=openrouter_api_key,
  default_headers={
    "HTTP-Referer": os.getenv("RENDER_URL", "http://localhost:8501"), 
    "X-Title": "MCP Attack Demo Chatbot",
  },
)

st.set_page_config(page_title="MCP Chatbot", page_icon="🤖")
st.title("🤖 MCP Chatbot with Scientific Calculator")

if not openrouter_api_key:
    st.error("`OPENROUTER_API_KEY` environment variable not set.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question or calculate something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ""
        math_task = detect_math_tool_and_extract_args(prompt)

        if math_task:
            tool_name, params = math_task
            with st.spinner(f"Calling calculator for **{tool_name}**..."):
                response = asyncio.run(call_mcp_tool(tool_name, params))
        else:
            with st.spinner("Thinking..."):
                try:
                    completion = client.chat.completions.create(
                        model="mistralai/mistral-7b-instruct:free",
                        messages=[
                            {"role": "system", "content": "You are a helpful and friendly assistant."},
                            *st.session_state.messages
                        ]
                    )
                    response = completion.choices[0].message.content
                except Exception as e:
                    response = f"Sorry, an error occurred with the AI model: {e}"
        
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
