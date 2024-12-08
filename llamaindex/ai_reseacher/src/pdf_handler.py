import os
import pickle
from llama_parse import LlamaParse
import requests
def parse_and_cache_pdfs(selected_papers):
    os.makedirs("data/papers", exist_ok=True)
    os.makedirs("data/parsed_docs", exist_ok=True)
    llama_parse = LlamaParse(result_type="markdown", num_workers=4, verbose=True)

    parsed_docs = []
    for paper in selected_papers:
        paper_id_safe = paper['id'].split("/")[-1]
        pdf_path = f"data/papers/{paper_id_safe}.pdf"
        parsed_doc_path = f"data/parsed_docs/{paper_id_safe}.pkl"
        if not os.path.exists(pdf_path):
            try:
                response = requests.get(paper['url'])
                response.raise_for_status()
                with open(pdf_path,'wb') as f:
                    f.write(response.content)
            except requests.exceptions.RequestException as e:
                print(f"Failed to download PDF for {paper['title']}: {e}")
                continue
        else:
            print(f"Using cached PDF for {paper['title']}")
            
        
        if os.path.exists(parsed_doc_path):
            print(f"Using cached Markdown for {paper['title']}")
            with open(parsed_doc_path, 'rb') as f:
                document = pickle.load(f)
        else:
            try:
                document = llama_parse.load_data(pdf_path)
                with open(parsed_doc_path, 'wb') as f:
                    pickle.dump(document, f)
                print(f"Parsed and cached document for {paper['title']} at {parsed_doc_path}")
            except Exception as e:
                print(f"Failed to parse {paper['title']}: {e}")
                continue
        parsed_docs.append(document)
                
    return parsed_docs
