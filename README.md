# 🚀 LangGraph MCP Chat App

## An advanced AI chatbot application built using:
- LangGraph (state-machine AI orchestration)
- MCP (Multi-Server Tool Protocol) for external tools
- Tavily Web Search
- Custom Stock Price Tool
- Weather API MCP Server
- Calculator MCP Server
- Streamlit UI with real-time streaming
This project demonstrates how to build a production-ready AI assistant that can call tools, fetch external data, and maintain multi-thread chat history — all with fast LLM inference powered by Groq.

<img width="1220" height="541" alt="Screenshot 2025-12-05 162741" src="https://github.com/user-attachments/assets/77a8f9bc-df3d-4df8-bc46-f9ece7c0fb63" />

## 📌 Features
### ✅ 1. LangGraph-Based AI Agent

- LLM node + tool execution node
- Automatic tool routing via tools_condition
- Persistent conversation memory per thread_id
- SQLite checkpointing

### ✅ 2. MCP Multi-Server Tools

This app runs multiple external tools using MCP:

- Tool	File	Description
- Arithmatic MCP Server	via MCP	Runs calculator logic
- Weather API MCP Server	via MCP	Uses OpenWeather API
- 
### ✅ 3. Custom Python Tools
🔹 Get Stock Price Tool

Fetch stock quotes using Alpha Vantage API:

@tool
def get_stock_price(symbol: str) -> dict:

### ✅ 4. Built-in Tavily Web Search Tool

Searches the web using Tavily:

web_search = TavilySearch(max_results=5)

Used for: news, general answers, factual queries, cricket schedule searches, etc.

### ✅ 5. Groq LLM Integration

Uses the openai/gpt-oss-20b model with ultra-fast inference , Use any model as per your choice

### ✅ 6. Streamlit Frontend

- Chat interface similar to ChatGPT
- Assistant real-time streaming
- Tool execution indicators (🔧 Using tool...)
- Multi-thread chat history
- Sidebar for switching chat threads

### ✅ 7. Async Execution Engine

- A dedicated asynchronous event-loop handles:
- LangGraph streaming
- MCP server tool calls
- Non-blocking Streamlit UI updates

## ⚙️ Setup Instructions
### 1. Clone the Repository
```
git clone https://github.com/Abhishek3689/Langgraph-MCP-Chat-App.git
```
### 2.Install Dependencies
```
pip install -r requirements.txt
```
### 3. Add Api Keys
Create a .env file:
```
WEATHER_API_KEY=your_openweather_key
TAVILY_API_KEY=your_tavily_key
ALPHAVANTAGE_API_KEY=your_alpha_vantage_key
GROQ_API_KEY=your_groq_key
```
### 4. Run Streamlit App
```
streamlit run mcp_server_langgraph_frontend.py
```
  
