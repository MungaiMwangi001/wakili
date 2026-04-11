"""
scripts/load_knowledge_base.py
Pre-loads Kenyan legal documents into ChromaDB using PersistentClient.
Run locally or triggered automatically on startup.
"""
import os
import sys

sys.path.insert(0, "/app")

from sentence_transformers import SentenceTransformer
from app.core.config import settings
import chromadb


BUILT_IN_KB = [
    {
        "source": "Employment Act 2007 – Kenya",
        "text": """The Employment Act 2007 of Kenya governs employment relationships.
Key provisions:
- Section 35: Termination requires notice. For monthly paid employees, minimum 28 days notice.
- Section 36: Summary dismissal is allowed only for gross misconduct such as theft, assault, or insubordination.
- Section 27: Maximum working hours are 52 per week, or 60 with overtime consent.
- Section 31: Employees are entitled to 21 days annual leave after 12 months of continuous service.
- Section 29: Maternity leave is 3 months (91 days) on full pay.
- Section 30: Paternity leave is 2 weeks.
- Wrongful termination: Employer must show valid reason and follow fair procedure.
- Redundancy: Employer must give 1 month notice, pay 15 days per year of service, and notify the Labour Officer.""",
    },
    {
        "source": "Contract Act Cap 23 – Kenya",
        "text": """The Law of Contract Act (Cap 23) governs contracts in Kenya.
Key provisions:
- A valid contract requires: offer, acceptance, consideration, capacity, and legality.
- Minors (under 18) lack capacity to contract except for necessities.
- A contract induced by misrepresentation, fraud, or undue influence is voidable.
- Penalty clauses that are punitive may be struck down by courts.
- Force majeure clauses excuse performance when unforeseen events make performance impossible.""",
    },
    {
        "source": "Consumer Protection Act 2012 – Kenya",
        "text": """The Consumer Protection Act 2012 protects consumers in Kenya.
- Section 55: Unfair contract terms are prohibited.
- Section 56: Auto-renewal clauses must be clearly disclosed.
- Section 74: Suppliers cannot exclude liability for death or personal injury caused by negligence.
- Section 87: Consumers may rescind contracts within 5 business days.""",
    },
    {
        "source": "Land Act 2012 – Kenya",
        "text": """The Land Act 2012 governs land transactions in Kenya.
- Section 79: Leases of more than 2 years must be in writing and registered.
- Section 90: A landlord must give 6 months notice before terminating a lease.
- Section 107: A purchaser must conduct due diligence at the Land Registry.""",
    },
    {
        "source": "Common Kenyan Contract Risk Flags",
        "text": """Common risk flags in Kenyan contracts:
1. Unlimited liability clauses may not be enforceable.
2. Termination ambiguity gives excessive power to one party.
3. Auto-renewal traps with short notice windows may be unfair.
4. Unilateral variation clauses are a red flag.
5. Foreign jurisdiction clauses may disadvantage Kenyan parties.
6. Broad indemnity clauses are risky.
7. Non-compete clauses must be reasonable in scope and time.
8. Excessive penalty clauses may be unenforceable under Cap 23.""",
    },
]


def load_knowledge_base():
    print(f"Using ChromaDB at: {settings.CHROMA_PERSIST_DIR}")
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

    try:
        client.delete_collection(settings.KB_COLLECTION_NAME)
        print(f"Deleted existing collection: {settings.KB_COLLECTION_NAME}")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=settings.KB_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print("Loading embedding model...")
    model = SentenceTransformer(settings.EMBEDDING_MODEL)

    all_texts = [e["text"] for e in BUILT_IN_KB]
    all_metadatas = [{"source": e["source"], "chunk_index": i} for i, e in enumerate(BUILT_IN_KB)]
    all_ids = [f"kb_builtin_{i}" for i in range(len(BUILT_IN_KB))]

    # Load any PDF/txt/docx files from knowledge_base/ directory
    kb_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    if os.path.exists(kb_dir):
        from app.services.text_extractor import extract_text
        from app.services.chunker import chunk_text

        for filename in os.listdir(kb_dir):
            if not filename.endswith((".pdf", ".txt", ".docx")):
                continue
            filepath = os.path.join(kb_dir, filename)
            ext = filename.rsplit(".", 1)[-1].lower()
            print(f"Loading KB file: {filename}")
            try:
                text = extract_text(filepath, ext)
                chunks = chunk_text(text, chunk_size=600, overlap=80)
                for chunk in chunks:
                    idx = len(all_texts)
                    all_texts.append(chunk["text"])
                    all_metadatas.append({"source": filename.rsplit(".", 1)[0], "chunk_index": idx})
                    all_ids.append(f"kb_file_{idx}")
            except Exception as e:
                print(f"  Warning: could not load {filename}: {e}")

    print(f"Embedding {len(all_texts)} chunks...")
    embeddings = model.encode(
        all_texts,
        show_progress_bar=True,
        normalize_embeddings=True
    ).tolist()

    collection.add(
        ids=all_ids,
        embeddings=embeddings,
        documents=all_texts,
        metadatas=all_metadatas,
    )
    print(f"\n✅ Knowledge base loaded: {len(all_texts)} chunks in '{settings.KB_COLLECTION_NAME}'")


if __name__ == "__main__":
    load_knowledge_base()