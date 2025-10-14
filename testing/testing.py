from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_chroma import Chroma
from api import API
from langchain.schema.runnable import Runnable
import random
from tqdm import tqdm
import os
from dotenv import load_dotenv
from openai import OpenAI
import time
from embedder import OpenAIEmbeder
import json
# Load environment variables from .env file
load_dotenv()


def ingest():
    # Get the doc
    loader = PyPDFLoader("testing/codigo_penal.pdf")
    pages = loader.load_and_split()
    # Split the pages by char
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(pages)
    print(f"Split {len(pages)} documents into {len(chunks)} chunks.")
    
    embedding = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    
    # Create vector store
    Chroma.from_documents(documents=chunks,  embedding=embedding, persist_directory="./sql_chroma_db")

def rag_chain(model: API) -> Runnable:

    prompt = PromptTemplate.from_template(
        """
        You are a friendly assistant. Answer the question based only on the following context. 
        If you don't know the answer, then reply, No Context availabel for this question {input}.
        Question: {input} 
        Context: {context} 
        Answer:
        """
    )
    # Load vector store
    embedding = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    # print size of embedding
    vector_store = Chroma(persist_directory="./sql_chroma_db", embedding_function=embedding)

    # Create chain
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 3,
            "score_threshold": 0.2,
        },
    )

    temp_prompt = "Knowledge of concurrence after the crime"
    docs = retriever.get_relevant_documents(temp_prompt)
    print("-------") # Testing stuff with rag.. irrelevant to the challenge
    for d in docs:
        print(d.page_content)
        print("-------")
    return None


if __name__ == "__main__":
    # ingest()

    exit()
    deepseek_api = API()
    rag_chain(deepseek_api)
    