# streamlit_app/app.py
import streamlit as st
from streamlit_app.components.auth import check_authentication
from streamlit_app.pages import prompt_editor, prompt_testing, execution_logs, feedback

st.set_page_config(
    page_title="PromptHub",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Authentication
    if not check_authentication():
        st.stop()
    
    # Sidebar Navigation
    st.sidebar.title("PromptHub")
    page = st.sidebar.selectbox(
        "Navigation",
        ["Prompt Editor", "Test Prompts", "Execution Logs", "Feedback Dashboard"]
    )
    
    # Page Routing
    if page == "Prompt Editor":
        prompt_editor.render()
    elif page == "Test Prompts":
        prompt_testing.render()
    elif page == "Execution Logs":
        execution_logs.render()
    elif page == "Feedback Dashboard":
        feedback.render()

if __name__ == "__main__":
    main()