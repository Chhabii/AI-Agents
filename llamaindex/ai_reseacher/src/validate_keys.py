import openai
import requests
from llama_cloud.client import LlamaCloud

def check_openai_api_key(api_key):
    client = openai.OpenAI(api_key=api_key)
    try:
        client.models.list()
    except openai.AuthenticationError:
        return False
    else:
        return True
    
    
def check_llama_cloud_api_key(api_key):
    try:
        client = LlamaCloud(token=api_key)
        projects = client.projects.list_projects()
        if client:
            return True
    except Exception:
        return False