from llama_cloud.types import CloudDocumentCreate
from pydantic import BaseModel, Field
from typing import List
from llama_cloud.client import LlamaCloud
from llama_index.core.prompts import PromptTemplate
from llama_index.core.async_utils import run_jobs
import os
from src.llm_utils import get_llm
from llama_parse import LlamaParse
from llama_index.indices.managed.llama_cloud import LlamaCloudIndex


llm = get_llm()


embedding_config = {
    "type": "OPENAI_EMBEDDING",
    "component": {
        "api_key": os.environ["OPENAI_API_KEY"],  # editable
        "model_name": "text-embedding-ada-002",  # editable
    },
}

# Transformation auto config
transform_config = {"mode": "auto", "config": {"chunk_size": 1024, "chunk_overlap": 20}}


def parse_pdf(pdf_files):
    llama_parse = LlamaParse(
        result_type="markdown",
        num_workers=4,  # if multiple files passed, split in `num_workers` API calls
        verbose=True,
    )
    documents = []

    for i, pdf_file in enumerate(pdf_files):
        print(f"Processing {i+1/len(pdf_files)}: ", {pdf_file})
        document = llama_parse.load_data(pdf_file)
        documents.append(document)
    return documents


class Metadata(BaseModel):
    author_names: List[str] = Field(
        ...,
        description="List of author names of the paper. Give empty list if not available.",
    )
    author_companies: List[str] = Field(
        ...,
        description="List of author companies of the paper. Give empty list if not available.",
    )
    ai_tags: List[str] = Field(
        ...,
        description="List of AI tags of the paper. Give empty list if not available.",
    )


def create_llamacloud_pipeline(
    pipeline_name, embedding_config, transform_config, data_sink_id=None
):
    client = LlamaCloud(token=os.environ["LLAMA_CLOUD_API_KEY"])
    pipeline = {
        "name": pipeline_name,
        "embedding_config": embedding_config,
        "transform_config": transform_config,
        "data_sink_id": data_sink_id,
    }
    pipeline = client.pipelines.upsert_pipeline(request=pipeline)
    return client, pipeline


async def get_papers_metadata(text):
    prompt_template = PromptTemplate(
        """Generate authors names, authors companies, and general top 3 AI tags for the given research paper.

    Research Paper:

    {text}"""
    )

    metadata = await llm.astructured_predict(
        Metadata,
        prompt_template,
        text=text,
    )
    return metadata


async def get_document_upload(document, llm):
    text_for_metadata = document[0].text + document[1].text + document[2].text
    metadata = await get_papers_metadata(text_for_metadata)
    full_text = "\n\n".join([doc.text for doc in document])

    cloud_document = CloudDocumentCreate(
        text=full_text,
        metadata={
            "author_names": metadata.author_names,
            "author_companies": metadata.author_companies,
            "ai_tags": metadata.ai_tags,
        },
    )
    return cloud_document


async def upload_documents(documents):
    extract_jobs = []
    for document in documents:
        extract_jobs.append(get_document_upload(document, llm))
    document_upload_objs = await run_jobs(extract_jobs, workers=4)
    client, pipeline = create_llamacloud_pipeline(
        "new_index", embedding_config, transform_config
    )
    _ = client.pipelines.create_batch_pipeline_documents(
        pipeline.id, request=document_upload_objs
    )


def index_as_query_engine():

    # Connects to a pre-built index in the Llama Cloud platform.
    index = LlamaCloudIndex(
        name="new_index",
        project_name="Default",
        api_key=os.environ["LLAMA_CLOUD_API_KEY"],
    )

    query_engine = index.as_query_engine(  # Configures a query engine to search the index.
        dense_similarity_top_k=10,  # Top k results based on dense (vector) similarity.
        sparse_similarity_top_k=10,  # Top k results based on sparse (keyword-based) similarity.
        alpha=0.5,  # Balances dense and sparse results (0 = only sparse, 1 = only dense).
        enable_reranking=True,  # Reranks results to improve relevance.
        rerank_top_n=5,  # Number of top results to rerank
        retrieval_mode="chunks",  # retrieves text in smaller units (e.g., paragraphs).
    )
    return query_engine
