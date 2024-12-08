import streamlit as st
from src.validate_keys  import check_openai_api_key, check_llama_cloud_api_key
from src.arxiv_handler import fetch_papers
from src.outline_generator import generate_default_outline
from src.report_generator import generate_report
import asyncio

import nest_asyncio
nest_asyncio.apply()

async def main():

    st.set_page_config(page_title="AI Research Assistant", layout="wide")
    st.sidebar.title("Settings")


    if "validate_openai_api_key" not in st.session_state:
        st.session_state.validate_openai_api_key = False
    if "validate_llama_cloud_api_key" not in st.session_state:
        st.session_state.validate_llama_cloud_api_key = False
        
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""
    if "llama_cloud_api_key" not in st.session_state:
        st.session_state.llama_cloud_api_key = ""

    if "papers" not in st.session_state:
        st.session_state.papers = []
    if "selected_papers" not in st.session_state:
        st.session_state.selected_papers = []
        
    if "outline" not in st.session_state:
        st.session_state.outline = ""

    if "outline_entered" not in st.session_state:
        st.session_state.outline_entered = False

    openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
    llama_cloud_api_key = st.sidebar.text_input("Enter your Llama Cloud API Key", type="password")

    st.session_state.openai_api_key = openai_api_key
    st.session_state.llama_cloud_api_key = llama_cloud_api_key

    validate_button = st.sidebar.button("Validate Keys")
    if validate_button:
        if not st.session_state.openai_api_key.strip():
            st.sidebar.error("Please enter your OpenAI API Key.")
        elif not st.session_state.llama_cloud_api_key.strip():
            st.sidebar.error("Please enter your Llama Cloud API Key.")
        else:
            st.session_state.validate_openai_api_key = check_openai_api_key(st.session_state.openai_api_key)
            st.session_state.validate_llama_cloud_api_key = check_llama_cloud_api_key(st.session_state.llama_cloud_api_key)
            
            if not st.session_state.validate_openai_api_key:
                st.sidebar.error("Invalid OpenAI API Key.")
                
            if not st.session_state.validate_llama_cloud_api_key:
                st.sidebar.error("Invalid Llama Cloud API Key.")


    if  st.session_state.validate_openai_api_key and st.session_state.validate_llama_cloud_api_key:
        st.sidebar.success("API Keys loaded successfully!",icon="✅")
        tab1, tab2 = st.tabs(["Workflow", "AI Agent"])
        with tab1:
            st.image("/home/chhabi/Desktop/engineering/agents/llamaindex/ai_reseacher/assets/final_agent_image.jpg", caption="Research Workflow", use_container_width=True)
        with tab2:
            st.header("Retrieve Papers")
            cols = st.columns(5)
            with cols[0]:
                tags = st.text_input("Enter tags (comma-separated)", value="RAG, AI Agent")
            with cols[1]:
                num_papers = st.number_input("Number of papers to fetch per tag", min_value=1, max_value=5, value=2)
            
            if st.button("Fetch Papers"):
                with st.spinner("Fetching papers..."):
                    st.session_state.papers = fetch_papers(tags, num_papers)
                    if st.session_state.papers:
                        st.success(f"{len(st.session_state.papers)} papers retrieved!")
                                
            st.markdown("---")
            if "papers" in st.session_state and st.session_state.papers:
                paper_cols = st.columns(2)

                with paper_cols[0]:
                    st.markdown("### Available Papers")
                    for paper in st.session_state.papers:
                        paper_key = f"paper_{paper['id']}"
                        if paper_key not in st.session_state:
                            st.session_state[paper_key] = False

                        if st.checkbox(f"{paper['title']} - {paper['authors']}", key=paper_key):
                            if paper not in st.session_state.selected_papers:
                                st.session_state.selected_papers.append(paper)
                        else:
                            if paper in st.session_state.selected_papers:
                                st.session_state.selected_papers.remove(paper)
                    

                with paper_cols[1]:
                    st.markdown("### Selected Papers")
                    if st.session_state.selected_papers:
                        for selected_paper in st.session_state.selected_papers:
                            st.write(f"✅ {selected_paper['title']} by {selected_paper['authors']}")
                    else:
                        st.info("No papers selected yet.")

            if st.session_state.selected_papers:
                st.subheader("Outline")
                default_outline = generate_default_outline(st.session_state.selected_papers)

                user_outline = st.text_area(
                    "Edit your outline below for the final report:",
                    value=default_outline,
                    key="user_outline",
                    height=300,
                )

                if st.button("Save Outline"):
                    st.session_state.outline = user_outline
                    st.success("Outline saved successfully!")
        
        
        if st.session_state.selected_papers and st.button("Generate Report"):
            with st.spinner("Generating the report..."):
                report = await generate_report(selected_papers = st.session_state.selected_papers, outline = st.session_state.outline, openai_api_key = st.session_state.openai_api_key)
                st.markdown(report)


if __name__ == "__main__":
    asyncio.run(main())