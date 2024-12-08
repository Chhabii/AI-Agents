import re
from src.llm_utils import get_llm
llm = get_llm()
def extract_title(outline):
    first_line = outline.strip().split("\n")[0]
    return first_line.strip("# ").strip()

    
def generate_query_with_llm(title,section, subsection):
    prompt = f"Generate a research query for a report on {title}. "
    prompt += f"The query should be for the subsection '{subsection}' under the main section '{section}'. "
    prompt += "The query should guide the research to gather relevant information for this part of the report. The query should be clear, short and concise. "
    
    response = llm.complete(prompt)

    return str(response).strip()

def classify_query(query):
    """Function to classify the query as either 'LLM' or 'INDEX' based on the query content"""

    prompt = f"""Classify the following query as either "LLM" if it can be answered directly by a large language model with general knowledge, or "INDEX" if it likely requires querying an external index or database for specific or up-to-date information.

    Query: "{query}"

    Consider the following:
    1. If the query asks for general knowledge, concepts, or explanations, classify as "LLM".
    2. If the query asks for specific facts, recent events, or detailed information that might not be in the LLM's training data, classify as "INDEX".
    3. If unsure, err on the side of "INDEX".

    Classification:"""
    
    classification = str(llm.complete(prompt)).strip().upper()
    if classification not in ["LLM", "INDEX"]:
        classification = "INDEX"
    return classification

def parse_outline_and_generate_queries(outline):
    lines = outline.strip().split("\n")
    title = extract_title(outline)
    current_section = ""
    queries = {}
    
    for line in lines[1:]:
        if line.startswith("## "):
            current_section = line.strip("# ").strip()
            queries[current_section] = {}
            
        elif re.match(r'^\d+\.\d+\.', line):
            subsection = line.strip()
            query = generate_query_with_llm(title,current_section, subsection)
            classification = classify_query(query)
            queries[current_section][subsection] = {"query":query, "classification":classification}
    
    #handle the sections without subsections
    for section in queries:
        if not queries[section]:
            query = generate_query_with_llm(title,section, "General Overview")
            queries[section]['General'] = {"query":query, "classification":"LLM"}
    
    return queries  
            
            
