
import uuid
import queue
import asyncio
import streamlit as st
from mcp_server_langgraph_backend import chatbot,get_all_threads,submit_async_task
from langchain_core.messages import HumanMessage,AIMessage,BaseMessage,ToolMessage

# ------------------------------------------------------------
# Helper: Creates a unique thread ID for each new conversation
# ------------------------------------------------------------
def generate_id():
    id=uuid.uuid4()
    return id
# ------------------------------------------------------------
# Helper: Reset chat interface when user clicks "New Chat"
# - Creates a new thread ID
# - Clears chat history
# ------------------------------------------------------------
def reset_chat():
    thread_id=generate_id()
    st.session_state['thread_id']=thread_id
    add_thread(thread_id)
    st.session_state['chat_history']=[]
# ------------------------------------------------------------
# Helper: Add a thread to session list (if not already present)
# ------------------------------------------------------------
def add_thread(thread_id):
    if thread_id not in st.session_state['all_threads']:
        st.session_state['all_threads'].append(thread_id)

# ------------------------------------------------------------
# Load all messages for a saved thread from LangGraph checkpoint
# ------------------------------------------------------------
def load_conversation(thread_id):
    config={'configurable':{'thread_id':thread_id}}
    state=chatbot.get_state(config=config).values.get('messages',[])
    return state

# -----------------------------
#    STREAMLIT UI START
# -----------------------------
st.title("Chat with Langgraaph")

# ------------------------------------------------------------
# Initialize required session_state vars
# ------------------------------------------------------------
if 'chat_history' not in st.session_state:
    st.session_state['chat_history']=[]

if 'thread_id' not in st.session_state:
    st.session_state['thread_id']=generate_id()

if 'all_threads' not in st.session_state:
    st.session_state['all_threads']=get_all_threads()

add_thread(st.session_state['thread_id'])

# ------------------------------------------------------------
# Sidebar: Contains
# - New Chat button
# - List of previous chat threads
# Clicking a thread reloads its messages
# ------------------------------------------------------------
with st.sidebar:
    st.header("Click for Conversation")
    if st.button("New Chat"):
        reset_chat()
    st.subheader("My Conversations")
    col1, col2 = st.columns([1, 4])
    with col2:
        conversations = st.session_state['all_threads']
        for i, thread in enumerate(conversations[::-1]):
            with st.expander(f"Conversation {i+1}"):
                if st.button(f"Open {thread}"):
                    st.session_state['thread_id'] = thread
                    messages = load_conversation(thread)
                    temp_messages = []
                    for msg in messages:
                        if isinstance(msg, HumanMessage):
                            role = 'user'
                        else:
                            role = 'assistant'
                        temp_messages.append({'role': role, 'content': msg.content})
                    st.session_state['chat_history'] = temp_messages

    ##
        # if st.button("New Chat"):
        #     reset_chat()
        # for thread in st.session_state['all_threads'][::-1]:
        #     if st.button(str(thread)):
        #         st.session_state['thread_id']=thread
        #         messages=load_conversation(thread)
        #         temp_msg=[]
        #         for msg in messages:
        #             if isinstance(msg,HumanMessage):
        #                 role='user'
        #             else:
        #                 role='assistant'
        #             temp_msg.append({'role':role,'content':msg.content})
        #         st.session_state['chat_history']=temp_msg
#

# ------------------------------------------------------------
# Render previous chat history on screen
# ------------------------------------------------------------
for msg in st.session_state['chat_history']:
    with st.chat_message(msg['role']):
        st.text(msg['content'])

# ------------------------------------------------------------
# User input box
# ------------------------------------------------------------       
user_input=st.chat_input("Ask Query ")

if user_input:
    # Display user message
    with st.chat_message('user'):
        st.text(user_input)
        st.session_state['chat_history'].append({'role':'user','content':user_input})
    config={"configurable":{"thread_id":st.session_state['thread_id']}}
    # Assistant streaming block
    with st.chat_message("assistant"):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            event_queue: queue.Queue = queue.Queue()

            async def run_stream():
                try:
                    async for message_chunk, metadata in chatbot.astream(
                        {"messages": [HumanMessage(content=user_input)]},
                        config=config,
                        stream_mode="messages",
                    ):
                        event_queue.put((message_chunk, metadata))
                except Exception as exc:
                    event_queue.put(("error", exc))
                finally:
                    event_queue.put(None)

            submit_async_task(run_stream())

            while True:
                item = event_queue.get()
                if item is None:
                    break
                message_chunk, metadata = item
                if message_chunk == "error":
                    raise metadata

                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    # Save assistant message
    st.session_state["chat_history"].append(
        {"role": "assistant", "content": ai_message}
    )