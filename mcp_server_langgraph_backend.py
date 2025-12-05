import sqlite3
import aiosqlite
import asyncio
import json
import threading
import requests 
from dotenv import load_dotenv
from langchain_core.tools import tool,BaseTool
from langgraph.graph import StateGraph,START,END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage,HumanMessage,AIMessage,ToolMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from pydantic import BaseModel,Field
from typing import List,Annotated,TypedDict
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_tavily import TavilySearch

load_dotenv()

# =================================================================
#  BACKGROUND ASYNC EVENT LOOP (for streaming + MCP servers)
# =================================================================
# LangGraph uses async operations, but Streamlit / Python scripts
# use a synchronous main thread.
# We create a dedicated async loop that runs forever on a background thread.
# Any async function can then be scheduled onto this loop.
_ASYNC_LOOP = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()

def _submit_async(coro):
    """
    Schedule an async coroutine to run on the background event loop.
    Returns a concurrent.futures.Future object.
    """
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)

def run_async(coro):
    """Run an async coroutine and wait for its result (synchronously)."""
    return _submit_async(coro).result()

def submit_async_task(coro):
    """Schedule a coroutine on the backend event loop."""
    return _submit_async(coro)

# =================================================================
#  BUILT-IN TOOL: Tavily Web Search
# =================================================================
web_search=TavilySearch(max_results=5)
# =================================================================
#  CUSTOM TOOL: Stock Price Lookup
# =================================================================
@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    return r.json()

# =================================================================
#  MCP (Multi-Server Control Protocol) TOOL SERVERS
#  These are external tools running as standalone processes.
# =================================================================
SERVERS={
    "Arithmatic": {
        "command": "uv",
        "args": [
            "run",
            "calculator.py"
        ],
        "env": {},
        "transport": "stdio"
    },
     "Weather_api": {
        "command": "uv",
        "args": [
            "run",
            "weather.py"
                ],
        "env": {"WEATHER_API_KEY": "9231e0f177bb4b7582445552250511"},
        "transport": "stdio"
        }
}


## model
llm=ChatGroq(model="openai/gpt-oss-20b")

# =================================================================
#  LOAD ALL MCP TOOLS dynamically
# =================================================================
client=MultiServerMCPClient(SERVERS)

def load_mcp_tools() -> list[BaseTool]:
    try:
        return run_async(client.get_tools())
    except Exception:
        return []
    
mcp_tools = load_mcp_tools()

# combine tools
tools = [web_search,get_stock_price, *mcp_tools]

# Bind tools to LLM → enables tool calling
llm_with_tools = llm.bind_tools(tools) if tools else llm

tool_node = ToolNode(tools) if tools else None
# =================================================================
#  CHECKPOINTING SYSTEM (conversation persistence)
# =================================================================
async def _init_checkpointer():
    conn = await aiosqlite.connect(database="chatbot.db")
    return AsyncSqliteSaver(conn)

checkpointer = run_async(_init_checkpointer())

# =================================================================
#  STATE STRUCTURE for LangGraph
# =================================================================
class Response_chat(TypedDict):
    messages:Annotated[List[BaseMessage],add_messages]

async def Chat_node(state: Response_chat):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}

# =================================================================
#  BUILD LANGGRAPH STATE MACHINE
# =================================================================
graph=StateGraph(Response_chat)
graph.add_node("Chat_node",Chat_node)
graph.add_edge(START,"Chat_node")

if tool_node:
    graph.add_node("tools", tool_node)
    graph.add_conditional_edges("Chat_node", tools_condition)
    graph.add_edge("tools", "Chat_node")
else:
    graph.add_edge("Chat_node", END)
    
chatbot=graph.compile(checkpointer=checkpointer)

# async def main():

#     # chatbot = await build_graph()
#     config={'configurable':{'thread_id':'thread_1'}}
#     result = await chatbot.ainvoke({"messages": [HumanMessage(content="What is current temperature of Mumbai")]},config=config)
#     last_response=result['messages'][-1]
#     print(result['messages'][-1].content)

# =================================================================
#  Retrieve all existing threads from SQLite checkpoint DB
# =================================================================
async def _alist_threads():
    all_threads = set()
    async for checkpoint in checkpointer.alist(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)

def get_all_threads():
    return run_async(_alist_threads())

