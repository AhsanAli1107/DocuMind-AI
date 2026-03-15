# main temp
import os
import tempfile
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core import StorageContext
import chromadb
import uvicorn
from typing import Optional, List
from dotenv import load_dotenv
import re

load_dotenv()

app = FastAPI(title="Document Q&A System")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    in_scope: bool

class UploadResponse(BaseModel):
    message: str
    filename: str

# Initialize models
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llama_llm = Groq(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    temperature=0.3,  # Lower temperature for more focused responses
    max_tokens=2000,
)

Settings.chunk_size = 1024
Settings.chunk_overlap = 50
Settings.llm = llama_llm
Settings.embed_model = embed_model

# ChromaDB setup
db = chromadb.PersistentClient(path="./chroma_db/test")
chroma_collection = db.get_or_create_collection(name="test")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Global variables
index = None
query_engine = None
current_document_text = ""  # Store current document text for validation

def create_index_from_directory(directory_path):
    global current_document_text
    documents = SimpleDirectoryReader(input_dir=directory_path, filename_as_id=True).load_data()
    
    # Store document text for validation
    current_document_text = " ".join([doc.text for doc in documents])
    
    new_index = VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context, 
        embed_model=embed_model, 
        show_progress=True
    )
    return new_index

def is_query_in_scope(query: str) -> bool:
    """
    Check if query is related to the uploaded document
    """
    global current_document_text
    
    if not current_document_text:
        return False
    
    # Create validation prompt
    validation_prompt = f"""
    Document Content (first 1000 chars): {current_document_text[:1000]}
    
    User Question: {query}
    
    Is this question asking for information that could be found in or derived from the document above?
    Answer with ONLY "YES" or "NO":
    """
    
    try:
        response = llama_llm.complete(validation_prompt)
        answer = response.text.strip().upper()
        return "YES" in answer
    except:
        # Fallback to simple check if LLM fails
        doc_words = set(current_document_text.lower().split())
        query_words = set(query.lower().split())
        common_words = doc_words.intersection(query_words)
        
        # If query shares at least 3 words with document
        return len(common_words) >= 3

@app.get("/")
async def root():
    return {"message": "Document Q&A System"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "document_loaded": index is not None
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        global index, query_engine
        
        # Validate file type
        allowed_types = ['pdf', 'txt', 'docx', 'md', 'csv']
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in allowed_types:
            raise HTTPException(status_code=400, detail=f"File type not allowed")
        
        # Create temp directory and save file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the uploaded file
        index = create_index_from_directory(temp_dir)
        query_engine = index.as_query_engine(llm=llama_llm, similarity_top_k=5)
        
        return UploadResponse(
            message="Document uploaded successfully! You can now ask questions about this document.",
            filename=file.filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        global query_engine
        
        if not query_engine:
            raise HTTPException(status_code=400, detail="Please upload a document first.")
        
        # Step 1: Check if query is in scope
        if not is_query_in_scope(request.query):
            return QueryResponse(
                response="I'm sorry, but I can only answer questions related to the uploaded document. Please ask something about the document you've provided.",
                in_scope=False
            )
        
        # Step 2: If in scope, get answer from document
        response = query_engine.query(request.query)
        
        return QueryResponse(
            response=str(response),
            in_scope=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Document Q&A System Started")
    print("📝 Only answers questions related to uploaded documents")
    print("⚡ Server running at: http://localhost:8000")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )