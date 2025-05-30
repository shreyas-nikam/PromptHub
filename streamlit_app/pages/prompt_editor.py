# streamlit_app/pages/prompt_editor.py
import streamlit as st
from streamlit_ace import st_ace
import requests

def render():
    st.title("Prompt Editor")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Prompt Selection
        prompt_id = st.selectbox("Select Prompt", get_prompts())
        
        # Editor Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Edit", "Dependencies", "Test", "History"])
        
        with tab1:
            # Main Prompt Editor
            prompt_content = st_ace(
                value=get_prompt_content(prompt_id),
                language='markdown',
                theme='monokai',
                key='prompt_editor',
                height=400
            )
            
            # Required Fields
            st.subheader("Required Fields")
            fields = st.data_editor(
                get_required_fields(prompt_id),
                num_rows="dynamic",
                column_config={
                    "name": st.column_config.TextColumn("Field Name"),
                    "type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["string", "number", "boolean", "array", "object"]
                    ),
                    "required": st.column_config.CheckboxColumn("Required"),
                    "description": st.column_config.TextColumn("Description")
                }
            )
            
            # Action Buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Save Draft", type="secondary"):
                    save_draft(prompt_id, prompt_content, fields)
            with col2:
                if st.button("Boost Prompt", type="secondary"):
                    boosted = boost_prompt(prompt_content)
                    st.session_state['boosted_prompt'] = boosted
            with col3:
                if st.button("Publish Version", type="primary"):
                    version = publish_version(prompt_id, prompt_content, fields)
                    st.success(f"Published version {version}")
        
        with tab2:
            # Dependencies Management
            st.subheader("System Prompt")
            system_prompt = st.text_area("System Prompt", height=150)
            
            st.subheader("Metaprompt")
            metaprompt = st.text_area("Metaprompt Template", height=150)
            
            st.subheader("Guardrails")
            pre_validation = st.text_area("Pre-invocation Validation", height=100)
            post_validation = st.text_area("Post-invocation Validation", height=100)
        
        with tab3:
            # Testing Interface
            test_prompt_interface(prompt_id)
        
        with tab4:
            # Version History
            show_version_history(prompt_id)
    
    with col2:
        # Sidebar Information
        st.subheader("Prompt Information")
        prompt_info = get_prompt_info(prompt_id)
        st.json(prompt_info)
        
        # Boosted Prompt Display
        if 'boosted_prompt' in st.session_state:
            st.subheader("Boosted Prompt")
            st.text_area(
                "Enhanced Version",
                st.session_state['boosted_prompt'],
                height=300
            )
            if st.button("Apply Boosted Version"):
                apply_boosted_prompt()