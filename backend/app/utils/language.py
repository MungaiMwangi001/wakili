"""
Language detection – detects English vs Swahili.
Uses langdetect + Swahili keyword heuristic for short queries.
"""
from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 42

SWAHILI_KEYWORDS = {
    "je", "nini", "wapi", "lini", "jinsi", "gani", "kwa", "na", "wa", "katika",
    "ni", "au", "ya", "za", "la", "kuhusu", "mkataba", "sheria", "haki",
    "wajibu", "mwajiri", "mfanyakazi", "malipo", "fidia", "masharti",
    "makubaliano", "hukumu", "mahakama", "ndio", "hapana", "tafadhali",
    "mshahara", "kumaliza", "pengo", "mkubaliano", "vipi", "bado", "sawa",
}


def detect_language(text: str) -> str:
    """Returns 'sw' for Swahili, 'en' for everything else."""
    text_lower = text.lower()
    sw_hits = sum(1 for w in text_lower.split() if w.strip("?.,!") in SWAHILI_KEYWORDS)
    if sw_hits >= 2:
        return "sw"
    try:
        lang = detect(text)
        return "sw" if lang in ("sw", "so") else "en"
    except LangDetectException:
        return "en"
