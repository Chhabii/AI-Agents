from llama_index.llms.openai import OpenAI
def get_llm():
    llm = OpenAI(model="gpt-4o-mini")
    return llm