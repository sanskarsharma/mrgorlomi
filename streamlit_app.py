import streamlit as st
from dotenv import load_dotenv
import random
import csv

load_dotenv()


participant_username = None
with open("data/participants.csv") as f:
    csv_reader = csv.reader(f)
    lines = list(csv_reader)
    line = random.choice(lines)
    participant_username, participant_full_name = line[0], line[1]


from llm.openai import OpenAILLM

llm = OpenAILLM()

if "user_id" in st.session_state:
    user_id = st.session_state["user_id"]
else:
    st.session_state["user_id"] = participant_username
    st.session_state["user_full_name"] = participant_full_name

if "llm_chain" not in st.session_state:
    # st.session_state["llm_app"] = bedrock
    st.session_state["llm_chain"] = llm.get_conversation_chain()

if "questions" not in st.session_state:
    st.session_state.questions = []

if "answers" not in st.session_state:
    st.session_state.answers = []

if "input" not in st.session_state:
    st.session_state.input = ""


def write_top_bar():
    col2, col3 = st.columns([12, 3])

    with col2:
        header = "Talk to Mr. Gorlomi"
        st.write(f"<h3 class='main-header'>{header}</h3>", unsafe_allow_html=True)
        st.write(f"<p>Mr Gorlomi (He pretends to be italian, pls entertain his sass) is here to help you with <i>teaming up for the hackathon</i></p>", unsafe_allow_html=True)
        st.write(f"<p>Your random assigned username for this session is <b>{st.session_state['user_full_name']}</b></p>", unsafe_allow_html=True)

    with col3:
        clear = st.button("Clear Chat")

    # Display user guidance
    with st.expander("🔍 What can I do?", expanded=True):
        st.markdown("""
            Here are the actions you can take:

            1. **Create a team**: Say something like "I want to create a team" or "Let's make a new team".
            2. **Join a team**: Say "I'd like to join a team" or "Can I join an existing team?".
            3. **List all teams**: Ask "What teams are there?" or "Show me all the teams".
            4. **Add an idea**: Say "I want to add an idea to my team" or "I have a new idea".
            5. **Edit an idea**: Say "I need to edit an idea" or "Can I change an idea?".
            6. **List team ideas**: Ask "What ideas does my team have?" or "Show me our ideas".
            7. **Leave a team**: Say "I want to leave my team" or "How do I exit my current team?".
            8. **Delete a team**: Say "I want to delete my team" (only for team captains).
            9. **Get help**: If you're unsure, just ask "What can I do?" or "Help me get started".

            Just type your request in the chat box below, and I'll guide you through the process!
            """
        )

    return clear


clear = write_top_bar()

if clear:
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.input = ""
    llm.clear_memory(st.session_state["llm_chain"])


def handle_input():
    input = st.session_state.input

    llm_chain = st.session_state["llm_chain"]
    result, amount_of_tokens = llm.get_conversation(chain=llm_chain, prompt=input, username=st.session_state["user_id"])
    question_with_id = {
        "question": input,
        "id": len(st.session_state.questions),
        "tokens": amount_of_tokens,
    }
    st.session_state.questions.append(question_with_id)

    st.session_state.answers.append(
        {"answer": result, "id": len(st.session_state.questions)}
    )
    st.session_state.input = ""


with st.container():
    for q, a in zip(st.session_state.questions, st.session_state.answers):
        
        # render question
        st.info(q["question"], icon="👤")

        # render answer
        chat = st.container()
        with chat:
            st.info(a["answer"], icon="🤖")
            st.markdown(f'<p style="text-align:right;"> Tokens used: {q["tokens"]} </p>', unsafe_allow_html=True)

input = st.text_input(
    f"Say stuff", key="input", on_change=handle_input
)
