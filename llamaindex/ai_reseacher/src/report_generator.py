from typing import Any
import re
from src.report_gen_utilities import extract_title, generate_query_with_llm, classify_query
from llama_index.core.llms.function_calling import FunctionCallingLLM
from src.llm_utils import get_llm
import asyncio
from src.pdf_handler import parse_and_cache_pdfs
from src.llama_parse_utils import upload_documents, index_as_query_engine
llm = get_llm()

class ReportGenerationAgent:
    def __init__(self,query_engine: Any, llm: FunctionCallingLLM):
        self.query_engine = query_engine
        self.llm = llm
    
    
    def parse_outline_and_generate_queries(self,outline):
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
    
    def generate_section_content(self,queries):
        sections_content = {}
        for section, subsections in queries.items():
            sections_content[section] = {}
            subsection_keys = subsections.keys()
            for subsection in subsection_keys:
                data = subsections[subsection]
                query = data['query']
                classification = data['classification']
                if classification == "LLM":
                    answer = str(self.llm.complete(query+"Give a short answer."))
                else:
                    answer = str(self.query_engine.query(query))
                sections_content[section][subsection] = answer
        return sections_content
    

    def format_report(self, sections_content, outline):
        report = ""
        introduction_content = None
        conclusion_content = None
        
        for section, subsections in sections_content.items():
            section_match = re.match(r'^(\d+\.)\s*(.*)$', section)
            if section_match:
                section_num, section_title = section_match.groups()
                
                
                if "introduction" in section.lower():
                    introduction_num, introduction_title = section_num, section_title
                    combined_intro_content = ("\n").join(subsections.values())
                    introduction_query = f"Refine and consolidate the introduction:\n\n{combined_intro_content}"
                    introduction_content = str(self.llm.complete(introduction_query))
                    continue 
                
                elif "conclusion" in section.lower():
                    conclusion_num, conclusion_title = section_num, section_title
                    combined_conclusion_content = ("\n").join(subsections.values())
                    conclusion_query = f"Refine and consolidate the conclusion:\n\n{combined_conclusion_content}"
                    conclusion_content = str(self.llm.complete(conclusion_query))
                    continue
                
                else:
                    combined_content = ("\n").join(subsections.values())
                    summary_query = f"Provide a short summary for section '{section}': \n\n {combined_content}"
                    section_summary = str(self.llm.complete(summary_query))
                    report += f"# {section_num} {section_title}\n\n {section_summary}\n\n"
                    
                    report = self.get_subsection_content(subsections, report)
        
        if introduction_content:
            report = f"# {introduction_num} {introduction_title}\n\n{introduction_content}\n\n" + report
        
        if conclusion_content:
            report += f"# {conclusion_num} {conclusion_title}\n\n{conclusion_content}\n\n"
        
        # Add title
        title = extract_title(outline)
        report = f"# {title}\n\n{report}"
        
        return report


    def get_subsection_content(self, subsections,report):
        for subsection in sorted(subsections.keys(), key=lambda x: re.search(r'(\d+\.\d+)', x).group(1) if re.search(r'(\d+\.\d+)', x) else x):
            content = subsections[subsection]
            subsection_match = re.search(r'(\d+\.\d+)\.\s*(.+)', subsection)
            if subsection_match:
                subsection_num, subsection_title = subsection_match.groups()
                report += f"## {subsection_num} {subsection_title}\n\n{content}\n\n"
            else:
                report += f"## {subsection}\n\n{content}\n\n"
        return report
    
    async def run_workflow(self,outline):
        queries = self.parse_outline_and_generate_queries(outline)
        sections_content = self.generate_section_content(queries)
        report = self.format_report(sections_content, outline)
        return report


async def generate_report(selected_papers, outline, openai_api_key):
    docs = parse_and_cache_pdfs(selected_papers)
    await upload_documents(docs)
    query_engine = index_as_query_engine()
    
    agent = ReportGenerationAgent(query_engine, llm)
    report = asyncio.run(agent.run_workflow(outline))
    return report
    