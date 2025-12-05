import sqlite3
from dotenv import load_dotenv
from langgraph.graph import StateGraph,START,END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage,HumanMessage,AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from typing import List,Annotated,TypedDict

load_dotenv()

conn=sqlite3.connect("sample_db.db",check_same_thread=False)

checkpointer=SqliteSaver(conn=conn)

## llm 
llm=ChatGroq(model="openai/gpt-oss-20b")

class Response_chat(TypedDict):
    messages:Annotated[List[BaseMessage],add_messages]

def Chat_node(user_input:Response_chat):
    response=llm.invoke(user_input['messages'])
    return {'messages':[response]}

graph=StateGraph(Response_chat)

graph.add_node("Chat_node",Chat_node)

graph.add_edge(START,"Chat_node")
graph.add_edge("Chat_node",END)

chatbot=graph.compile(checkpointer=checkpointer)

# while True:
#     user_input=input("Ask Query :")
#     if user_input in ['exit','quit']:
#         break
#     result=chatbot.invoke({'messages':[HumanMessage(content=user_input)]},config=config)
#     print(result['messages'][-1].content)

def get_all_threads():
    set_threads=set()
    for thread in checkpointer.list(None):
        set_threads.add(thread.config['configurable']['thread_id'])
    return list(set_threads)
