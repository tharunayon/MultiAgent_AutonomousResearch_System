import os
import streamlit as st
import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# Embedding model dimension for 'all-MiniLM-L6-v2' is 384
EMBEDDING_DIMENSION = 384

@st.cache_resource
def get_embedding_model():
    """Loads the sentence transformer embedding model. Caches the model resource in Streamlit."""
    return SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_from_pdf(pdf_file) -> str:
    """Extracts text content page-by-page from an uploaded PDF file object."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF content: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 400, chunk_overlap: int = 50) -> list[str]:
    """Chunks input text into overlapping word tokens to maintain context at boundaries."""
    words = text.split()
    chunks = []
    i = 0
    step = max(1, chunk_size - chunk_overlap)
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) > 10:  # Ignore very small trailing fragments
            chunks.append(" ".join(chunk_words))
        i += step
    return chunks

def init_rag_state():
    """Initializes the FAISS indexes and document lists in Streamlit session state."""
    if "faiss_index_patient" not in st.session_state:
        st.session_state.faiss_index_patient = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    if "faiss_index_doctor" not in st.session_state:
        st.session_state.faiss_index_doctor = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    if "chunks_patient" not in st.session_state:
        st.session_state.chunks_patient = []
    if "chunks_doctor" not in st.session_state:
        st.session_state.chunks_doctor = []
    if "uploaded_documents" not in st.session_state:
        st.session_state.uploaded_documents = []

def clear_rag_state():
    """Resets all indices and uploaded documents."""
    st.session_state.faiss_index_patient = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    st.session_state.faiss_index_doctor = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    st.session_state.chunks_patient = []
    st.session_state.chunks_doctor = []
    st.session_state.uploaded_documents = []

def ingest_pdf(pdf_file, visibility: str) -> dict:
    """Extracts, chunks, embeds and saves a PDF into the appropriate FAISS index based on RBAC metadata."""
    init_rag_state()
    
    filename = os.path.basename(pdf_file.name)
    # Avoid duplicate file ingestion
    if any(doc["filename"] == filename for doc in st.session_state.uploaded_documents):
        return {"success": False, "message": f"Document '{filename}' is already ingested."}
        
    text = extract_text_from_pdf(pdf_file)
    if not text.strip():
        return {"success": False, "message": f"Could not extract readable text from '{filename}'."}
        
    chunks = chunk_text(text)
    if not chunks:
        return {"success": False, "message": f"Document '{filename}' did not yield enough chunks."}
        
    # Generate embeddings using the cached model
    model = get_embedding_model()
    embeddings = model.encode(chunks).astype("float32")
    
    # Map chunk metadata structure
    chunk_dicts = [
        {
            "text": chunk,
            "source": filename,
            "visibility": visibility
        }
        for chunk in chunks
    ]
    
    # Store indices based on visibility restriction rules
    if visibility == "public_patient":
        # Public data goes to both Patient index and Doctor index
        st.session_state.faiss_index_patient.add(embeddings)
        st.session_state.chunks_patient.extend(chunk_dicts)
        
        st.session_state.faiss_index_doctor.add(embeddings)
        st.session_state.chunks_doctor.extend(chunk_dicts)
    elif visibility == "doctor_only":
        # Restricted data goes ONLY to the Doctor index
        st.session_state.faiss_index_doctor.add(embeddings)
        st.session_state.chunks_doctor.extend(chunk_dicts)
    else:
        return {"success": False, "message": f"Invalid visibility class '{visibility}'."}
        
    # Save documents state
    st.session_state.uploaded_documents.append({
        "filename": filename,
        "visibility": visibility,
        "chunks_count": len(chunks)
    })
    
    return {
        "success": True,
        "message": f"Successfully ingested {len(chunks)} chunks from '{filename}' (Visibility: {visibility})."
    }

def search_rag(query: str, role: str, top_k: int = 4) -> list[dict]:
    """Retrieves relevant chunks by embedding the query and searching the user's role-authorized FAISS index."""
    init_rag_state()
    
    if not query.strip():
        return []
        
    # Determine search domain
    if role == "doctor":
        index = st.session_state.faiss_index_doctor
        chunks = st.session_state.chunks_doctor
    else:
        index = st.session_state.faiss_index_patient
        chunks = st.session_state.chunks_patient
        
    # Check if there are elements to search
    if index.ntotal == 0:
        return []
        
    # Embed search query
    model = get_embedding_model()
    query_vector = model.encode([query]).astype("float32")
    
    # Execute query search
    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_vector, k)
    
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx != -1 and idx < len(chunks):
            chunk_data = chunks[idx].copy()
            # In L2 index, lower distance = higher similarity
            chunk_data["score"] = float(dist)
            results.append(chunk_data)
            
    return results
