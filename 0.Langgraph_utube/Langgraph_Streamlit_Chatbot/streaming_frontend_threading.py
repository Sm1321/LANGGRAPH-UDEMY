import streamlit as st  # Streamlit for building the web app
from langgraph_backend import chatbot  # Importing the chatbot backend
from langchain_core.messages import HumanMessage  # Message type to represent user input
import uuid  # For generating unique thread IDs

# **************************************** utility functions *************************

# Generate a unique thread ID using UUID
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

# Resets the chat session: new thread, clears message history
def reset_chat():
    thread_id = generate_thread_id()  # Generate a new thread ID
    st.session_state['thread_id'] = thread_id  # Store it in session
    add_thread(st.session_state['thread_id'])  # Add thread ID to chat_threads if not already present
    st.session_state['message_history'] = []  # Clear current chat messages

# Add thread ID to the list if it's not already in session state
def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

# Load messages of a particular thread from the chatbot's backend state
def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']


# **************************************** Session Setup ******************************

# Initialize message history in session if not present
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Initialize thread ID in session if not present
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

# Initialize list to store all chat thread IDs
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

# Add the current thread ID to the list of chat threads
add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

# Sidebar title
st.sidebar.title('LangGraph Chatbot')

# Button to start a new chat (creates new thread and clears history)
if st.sidebar.button('New Chat'):
    reset_chat()

# Header for conversation history
st.sidebar.header('My Conversations')

# Loop through chat threads in reverse order and display each as a button
for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):  # If a thread button is clicked
        st.session_state['thread_id'] = thread_id  # Set selected thread as active
        messages = load_conversation(thread_id)  # Load its conversation from backend

        temp_messages = []  # Temporary list to store formatted messages

        for msg in messages:
            # Determine role based on message type
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            # Append formatted message to the list
            temp_messages.append({'role': role, 'content': msg.content})

        # Replace current message history with the selected thread's messages
        st.session_state['message_history'] = temp_messages


# **************************************** Main UI ************************************

# Display all messages from the current message history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):  # Show message in chat UI
        st.text(message['content'])

# Input box for the user to send a new message
user_input = st.chat_input('Type here')

# If user submits a message
if user_input:

    # Add user's message to message history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # Prepare thread ID config to send to backend
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # Display assistant response using streaming
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},  # Send user's message
                config= CONFIG,  # Send thread-specific config
                stream_mode= 'messages'  # Enable streaming of message chunks
            )
        )

    # Append assistant's message to message history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
