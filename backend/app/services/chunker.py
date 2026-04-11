"""
Text Chunker – splits extracted document text into overlapping chunks
suitable for RAG embedding (~800 tokens, 100 token overlap).
Uses tiktoken for accurate token counting.
"""
import re
import tiktoken
import structlog


log = structlog.get_logger()

_tokenizer = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[dict]:
    """
    Split text into overlapping chunks with metadata.
    Returns list of {"text": str, "chunk_index": int, "token_count": int}
    """
    text = _clean_text(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    chunks = []
    current_tokens: list[int] = []
    chunk_index = 0

    for para in paragraphs:
        para_tokens = _tokenizer.encode(para)

        if len(para_tokens) > chunk_size:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sent in sentences:
                sent_tokens = _tokenizer.encode(sent)
                if len(current_tokens) + len(sent_tokens) > chunk_size:
                    if current_tokens:
                        chunks.append(_make_chunk(current_tokens, chunk_index))
                        chunk_index += 1
                        current_tokens = current_tokens[-overlap:]
                current_tokens.extend(sent_tokens)
        else:
            if len(current_tokens) + len(para_tokens) > chunk_size:
                if current_tokens:
                    chunks.append(_make_chunk(current_tokens, chunk_index))
                    chunk_index += 1
                    current_tokens = current_tokens[-overlap:]
            current_tokens.extend(para_tokens)

    if current_tokens:
        chunks.append(_make_chunk(current_tokens, chunk_index))

    log.info("Text chunked", chunk_count=len(chunks))
    return chunks


def _make_chunk(tokens: list[int], index: int) -> dict:
    text = _tokenizer.decode(tokens)
    clause_pattern = r"(?:Clause|Article|Section)\s*(\d+(?:\.\d+)?)"
    match = re.search(clause_pattern, text, re.IGNORECASE)
    clause_number = match.group(1) if match else None

    return {
        "text": text, 
        "chunk_index": index, 
        "token_count": len(tokens),
        "clause_number": clause_number # Added to metadata
    }

def _clean_text(text: str) -> str:
    text = re.sub(r"[^\x20-\x7E\n\r\t\u0080-\uFFFF]", " ", text)
    text = re.sub(r"\t", " ", text)
    text = re.sub(r" {3,}", "  ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()
