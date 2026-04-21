import streamlit as st
import subprocess
from src import config

# Page Configuration
st.set_page_config(
    page_title="Azure AI Foundry Agent RAG",
    page_icon="🤖",
    layout="centered"
)

# Sidebar
with st.sidebar:
    st.title("Project Info")
    st.markdown(f"**LLM:** `{config.LLM_MODEL}`")
    st.markdown(f"**Embeddings:** `{config.EMBED_MODEL}`")
    st.markdown("**Data source:** `documents/` directory")
    
    st.divider()
    
    if st.button("Re-index corpus"):
        with st.spinner("Re-indexing corpus..."):
            try:
                # Use the venv python to run the ingest script as requested by user
                result = subprocess.run(
                    [".venv\\Scripts\\python.exe", "scripts/ingest.py"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                st.success("Indexing complete!")
                # st.toast("Vector store updated successfully.")
            except subprocess.CalledProcessError as e:
                st.error(f"Indexing failed: {e.stderr}")

st.title("Azure AI Foundry Agent RAG")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Show welcome message if no history
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("Ask a question about the Microsoft Azure AI Foundry Agent Service. The agent will read the official docs and gather citations for you.")

from src.agent import compile_graph

# Compile the graph once
graph = compile_graph()

# Accept user input
if prompt := st.chat_input("Ask a question about the Microsoft Azure AI Foundry Agent Service..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        # Placeholder for streaming status and response
        response_placeholder = st.empty()
        
        with st.status("Evaluating document relevance...", expanded=True) as status:
            state = {"question": prompt, "retries": 0}
            node_labels = {
                "retrieve": "Searching knowledge base...",
                "grade": "Batch-grading retrieved documents...",
                "generate": "Synthesizing answer with citations...",
                "hallucination": "Verifying grounding...",
                "rewrite": "Reformulating query for better results...",
                "out_of_scope": "Handling out-of-scope query..."
            }
            # Stream the graph execution to show node steps
            for event in graph.stream(state):
                for node_name, node_update in event.items():
                    label = node_labels.get(node_name, f"Executing: {node_name}")
                    st.write(f"Step: **{label}**")
                    state.update(node_update)
            
            final_state = state
            status.update(label="Answer generated", state="complete", expanded=False)

        if final_state and "generation" in final_state:
            answer = final_state["generation"]
            st.markdown(answer)
            
            # Citation UX: Display sources in an expander if available
            if "documents" in final_state and final_state["documents"]:
                with st.expander("Sources & Context Chunks"):
                    st.caption("The following excerpts were used by the agent to construct the answer above.")
                    for i, doc_str in enumerate(final_state["documents"], 1):
                        # Extract source and section from the formatted doc string in agent.py
                        parts = doc_str.split("\n", 2)
                        source_label = parts[0].replace("SOURCE: ", "") if len(parts) > 0 else "Unknown"
                        section_label = parts[1].replace("SECTION: ", "") if len(parts) > 1 else "Unknown"
                        content_full = parts[2].replace("CONTENT: ", "") if len(parts) > 2 else ""
                        
                        st.markdown(f"#### [{i}] {source_label}")
                        st.markdown(f"**Section:** {section_label}")
                        st.info(content_full)
                        if i < len(final_state["documents"]):
                            st.divider()
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            error_msg = "Error: The agent failed to produce a response."
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
