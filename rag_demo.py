import os
import sys
import io
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from datetime import datetime
import hashlib

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fix for UnicodeEncodeError on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ---------------------------------------------------------
# 1. INITIALIZING GROQ LLM
# ---------------------------------------------------------
print("\n[STEP 1] Initializing Groq LLM...")
API_KEY = os.getenv("GROQ_API_KEY")


llm = ChatGroq(
    api_key=API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0
)
print("✅ Groq LLM (Llama-3.3) is ready.")

# ---------------------------------------------------------
# 2. DEFINING SOURCE FILES
# ---------------------------------------------------------
files_to_load = ["policy.txt", "terms.txt"]
INDEX_PATH = "faiss_index"
HASH_FILE = "faiss_index/files_hash.txt"

def get_files_hash(files):
    """Generate a combined hash of all input files to detect changes."""
    hasher = hashlib.md5()
    for file in files:
        if os.path.exists(file):
            with open(file, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()

current_hash = get_files_hash(files_to_load)
should_rebuild = True

# ---------------------------------------------------------
# 3. CREATING EMBEDDINGS (Local Model)
# ---------------------------------------------------------
print("\n[STEP 3] Initializing Embeddings model...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print("✅ Embeddings model ready.")

# ---------------------------------------------------------
# 4. SMART LOAD OR REBUILD
# ---------------------------------------------------------
if os.path.exists(INDEX_PATH) and os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r") as f:
        stored_hash = f.read().strip()
    
    if stored_hash == current_hash:
        print(f"\n[STEP 4] Loading existing Vector Store (Files unchanged)...")
        vector_store = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        print("✅ Vector store loaded from disk. Skipped processing steps.")
        should_rebuild = False
    else:
        print(f"\n[STEP 4] Changes detected in source files! Rebuilding...")

if should_rebuild:
    # --- STEP 4a: LOADING DOCUMENTS ---
    print("\n[STEP 4a] Loading Policy and Terms documents...")
    docs = []
    for file in files_to_load:
        try:
            loader = TextLoader(file, encoding="utf-8")
            docs.extend(loader.load())
            print(f"   - Loaded {file}")
        except Exception as e:
            print(f"   - ❌ Error loading {file}: {e}")

    # --- STEP 4b: LINE-BASED SPLITTING ---
    print("\n[STEP 4b] Splitting documents by lines (Point-by-Point)...")
    # We use \n as the main separator to keep each bullet point intact
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n"], 
        chunk_size=200, 
        chunk_overlap=0 # No overlap needed for independent rules
    )
    chunks = text_splitter.split_documents(docs)
    print(f"   - Created {len(chunks)} chunks (one for each rule/point).")

    # --- STEP 4c: BUILDING INDEX ---
    print("\n[STEP 4c] Building and Saving Vector Store...")
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(INDEX_PATH)
    
    # Save hash
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    with open(HASH_FILE, "w") as f:
        f.write(current_hash)
    print(f"✅ Vector store rebuilt and saved to '{INDEX_PATH}'.")

# ---------------------------------------------------------
# 5. SETTING UP RETRIEVAL CHAIN
# ---------------------------------------------------------
print("\n[STEP 5] Setting up the Retrieval QA Chain...")
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

prompt_template = """
You are an insurance claim assessment system.

Claim Data:
{question}

Relevant Policy/Terms Context:
{context}

STRICT ASSESSMENT RULES:
1. T&C Rule 1: Claim MUST be reported within 7 days. If report delay is greater than 7, the decision MUST be 'Not Covered'.
2. Incident Type Check: If theft, check police complaint (within 24h).
3. Policy Coverage: Check if incident type is covered and not excluded.

Return ONLY raw JSON in this format:
{{
  "decision": "Covered" | "Not Covered" | "Needs Human Review",
  "justification": "Explain the decision.",
  "flags": []
}}
"""
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": PROMPT},
    return_source_documents=True
)
print("✅ Retrieval QA Chain is configured.")

# ---------------------------------------------------------
# 6. EXECUTING THE RAG PIPELINE
# ---------------------------------------------------------
print("\n[STEP 6] Running the RAG Pipeline...")

def extract_date(text, label):
    for line in text.splitlines():
        if label in line:
            return line.split(":")[1].strip()
    return None

with open("claim.txt", "r", encoding="utf-8") as f:
    claim_data = f.read()

# Pre-calculate delay
incident_date_str = extract_date(claim_data, "Incident Date")
report_date_str = extract_date(claim_data, "Report Date")
delay_days = "Unknown"
if incident_date_str and report_date_str:
    try:
        d1 = datetime.strptime(incident_date_str, "%Y-%m-%d")
        d2 = datetime.strptime(report_date_str, "%Y-%m-%d")
        delay_days = (d2 - d1).days
    except:
        pass

enriched_claim = f"{claim_data}\n\nComputed Data:\n- Days between Incident and Report: {delay_days} days"

print("\n🔍 Querying RAG and generating assessment...")
response = qa_chain.invoke(enriched_claim)

print("\n[SOURCES USED]")
for i, doc in enumerate(response["source_documents"]):
    # Show the full chunk to see how the line-splitting worked
    print(f"   {i+1}. {doc.metadata['source']}: \"{doc.page_content.strip()}\"")

print("\n" + "="*50)
print("FINAL RAG ASSESSMENT RESULT (JSON)")
print("="*50)
print(response["result"])
print("="*50)
print("\n[DEMO COMPLETE]")
