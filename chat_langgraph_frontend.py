import streamlit as st
from chat_langgraph_backend import chatbot,get_all_threads
from langchain_core.messages import HumanMessage,AIMessage,BaseMessage
import uuid

# list_threads=get_all_threads()

def generate_id():
    id=uuid.uuid4()
    return id

def reset_chat():
    thread_id=generate_id()
    st.session_state['thread_id']=thread_id
    add_thread(thread_id)
    st.session_state['chat_history']=[]
    
def add_thread(thread_id):
    if thread_id not in st.session_state['all_threads']:
        st.session_state['all_threads'].append(thread_id)

def load_conversation(thread_id):
    config={'configurable':{'thread_id':thread_id}}
    state=chatbot.get_state(config=config).values.get('messages',[])
    return state

st.title("Chat with Langgraaph")

if 'chat_history' not in st.session_state:
    st.session_state['chat_history']=[]

if 'thread_id' not in st.session_state:
    st.session_state['thread_id']=generate_id()

if 'all_threads' not in st.session_state:
    st.session_state['all_threads']=get_all_threads()

add_thread(st.session_state['thread_id'])

with st.sidebar:
    if st.button("New Chat"):
        reset_chat()
    for thread in st.session_state['all_threads'][::-1]:
        if st.button(str(thread)):
            st.session_state['thread_id']=thread
            messages=load_conversation(thread)
            temp_msg=[]
            for msg in messages:
                if isinstance(msg,HumanMessage):
                    role='user'
                else:
                    role='assistant'
                temp_msg.append({'role':role,'content':msg.content})
            st.session_state['chat_history']=temp_msg

for msg in st.session_state['chat_history']:
    with st.chat_message(msg['role']):
        st.text(msg['content'])
          
user_input=st.chat_input("Ask Query ")

if user_input:
    with st.chat_message('user'):
        st.text(user_input)
        st.session_state['chat_history'].append({'role':'user','content':user_input})
    config={"configurable":{"thread_id":st.session_state['thread_id']}}
    with st.chat_message('assistant'):
        ai_msg=[]
        for msg_chunk,metadata in chatbot.stream(
            {'messages':[HumanMessage(content=user_input)]},config=config,stream_mode='messages'):
            ai_msg.append(msg_chunk.content)
        st.write_stream(ai_msg)
        st.session_state['chat_history'].append({'role':'assistant','content':' '.join(ai_msg)})