"""
scripts/load_knowledge_base.py
───────────────────────────────
Pre-loads Kenyan legal documents into the ChromaDB knowledge base collection.
Run this ONCE after first deployment, or whenever you add new KB documents.

Usage:
    docker exec wakili-backend-1 python scripts/load_knowledge_base.py

Place your Kenyan law PDFs in backend/knowledge_base/ before running.
Default documents included:
  - Employment Act 2007 summary
  - Contract Act Cap 23 summary
  - Consumer Protection Act 2012 summary
  - Common contract clauses reference
"""
import os
import sys
import chromadb

sys.path.insert(0, "/app")

from sentence_transformers import SentenceTransformer
from app.core.config import settings

# ── Built-in knowledge base texts ────────────────────────────────────────────
# These are loaded even if no PDF files are present.
# Add more entries as needed.

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
- Consideration must be adequate but need not be equal in value.
- Minors (under 18) lack capacity to contract except for necessities.
- A contract induced by misrepresentation, fraud, or undue influence is voidable.
- Penalty clauses that are punitive rather than compensatory may be struck down by courts.
- Liquidated damages clauses are enforceable if they represent a genuine pre-estimate of loss.
- Unlimited liability clauses may be challenged as unconscionable in consumer contracts.
- Force majeure clauses excuse performance when unforeseen events make performance impossible.""",
    },
    {
        "source": "Consumer Protection Act 2012 – Kenya",
        "text": """The Consumer Protection Act 2012 protects consumers in Kenya.
Key provisions:
- Section 55: Unfair contract terms are prohibited. A term is unfair if it causes significant imbalance.
- Section 56: Auto-renewal clauses must be clearly disclosed to consumers.
- Section 62: Consumers have the right to clear and plain language in contracts.
- Section 74: Suppliers cannot exclude liability for death or personal injury caused by negligence.
- Section 87: Consumers may rescind contracts entered into under false pretenses within 5 business days.
- Jurisdiction: Disputes may be referred to the Consumer Protection Advisory Committee.""",
    },
    {
        "source": "Land Act 2012 – Kenya",
        "text": """The Land Act 2012 governs land transactions in Kenya.
Key provisions:
- All land in Kenya is vested in the National Government in trust for the Kenyan people.
- Land may be public, community, or private.
- Section 79: Leases of more than 2 years must be in writing and registered.
- Section 90: A landlord must give 6 months notice before terminating a lease.
- Section 107: A purchaser of land must conduct due diligence including a search at the Land Registry.
- Caution: A caution may be registered to protect an interest in land pending resolution of a dispute.
- The National Land Commission oversees public land and investigates historical injustices.""",
    },
    {
        "source": "Common Kenyan Contract Risk Flags",
        "text": """Common risk flags in Kenyan contracts:
1. Unlimited liability clauses: Clauses making one party liable for all loss without cap are high risk. Courts may not enforce them.
2. Termination ambiguity: Contracts that do not specify grounds or notice period for termination give excessive power to one party.
3. Auto-renewal traps: Clauses that automatically renew a contract unless notice is given within a short window may be unfair.
4. Unilateral variation: Clauses allowing one party to change terms without consent of the other are a red flag.
5. Jurisdiction clauses: Clauses specifying foreign jurisdiction or arbitration outside Kenya may disadvantage Kenyan parties.
6. Indemnification: Broad indemnity clauses requiring one party to indemnify the other for all claims, even caused by the indemnified party, are risky.
7. Non-compete clauses: Must be reasonable in scope, geography, and time. Courts will not enforce overly broad restrictions.
8. Penalty clauses: Excessive penalties not reflective of actual loss may be unenforceable under Cap 23.""",
    },
]


def load_knowledge_base():
    print("Connecting to ChromaDB...")
    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)

    # Delete and recreate the KB collection for a clean load
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

    all_texts = []
    all_metadatas = []
    all_ids = []
    chunk_index = 0

    # Load built-in texts
    for entry in BUILT_IN_KB:
        all_texts.append(entry["text"])
        all_metadatas.append({
            "source": entry["source"],
            "chunk_index": chunk_index,
        })
        all_ids.append(f"kb_builtin_{chunk_index}")
        chunk_index += 1

    # Load any PDF files from the knowledge_base/ directory
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
                    all_texts.append(chunk["text"])
                    all_metadatas.append({
                        "source": filename.replace("_", " ").replace("-", " ").rsplit(".", 1)[0],
                        "chunk_index": chunk_index,
                    })
                    all_ids.append(f"kb_file_{chunk_index}")
                    chunk_index += 1
            except Exception as e:
                print(f"  Warning: could not load {filename}: {e}")

    # Embed and index
    print(f"Embedding {len(all_texts)} knowledge base chunks...")
    embeddings = model.encode(all_texts, show_progress_bar=True, normalize_embeddings=True).tolist()

    collection.add(
        ids=all_ids,
        embeddings=embeddings,
        documents=all_texts,
        metadatas=all_metadatas,
    )

    print(f"\nKnowledge base loaded: {len(all_texts)} chunks in '{settings.KB_COLLECTION_NAME}'")
    print("Wakili will now use this as a fallback when document confidence is low.")


if __name__ == "__main__":
    load_knowledge_base()
