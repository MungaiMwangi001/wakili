"""
Groq LLM Service – all text generation via Groq API (free tier).
Supports conversation memory, knowledge base fallback flag, and legal disclaimer.

Fixes:
  - ask() now returns a well-formatted prose answer (not raw JSON) so the
    chat page renders readable text.
  - analyse() still returns structured JSON for the document viewer.
  - risk_flags now carry both `type`/`description` (document viewer) AND
    `risk_type`/`explanation` (chat bubble) so both renderers work.
  - clause_summaries carry both `text` (viewer) and `summary` (original).
"""
import json
import re
import structlog
from groq import Groq
from app.core.config import settings

log = structlog.get_logger()

DISCLAIMER_EN = (
    "\n\n---\n*This is AI-generated legal information, not legal advice. "
    "Please consult a qualified Kenyan advocate for your specific situation.*"
)
DISCLAIMER_SW = (
    "\n\n---\n*Hii ni taarifa ya kisheria inayotolewa na AI, si ushauri wa kisheria. "
    "Tafadhali wasiliana na wakili aliyestahili kwa hali yako maalum.*"
)

# ── Chat / Q&A system prompt ───────────────────────────────────────────────────
# The `answer` field must be readable prose — NOT a JSON dump.
SYSTEM_EN = """You are Wakili, an expert AI legal assistant specialising in Kenyan law.
You have retrieved contract clauses and the conversation history — use both.

Return ONLY valid JSON with NO markdown fences. Exact structure:
{
  "answer": "<Clear, well-structured plain-English answer. Use numbered lists or headings inside this string where helpful. NEVER put raw JSON here. Write as if explaining to a non-lawyer.>",
  "clause_summaries": [
    {"clause_number": 1, "title": "Clause title", "summary": "One sentence.", "text": "One sentence.", "language": "en"}
  ],
  "risk_flags": [
    {"clause_number": 1, "type": "Unlimited Liability", "risk_type": "unlimited_liability", "severity": "high", "description": "Plain-language explanation.", "explanation": "Plain-language explanation.", "language": "en"}
  ],
  "obligations": [
    {"party": "Employee", "obligation": "What they must do.", "condition": "When applicable.", "deadline": "By when.", "language": "en"}
  ]
}

Rules for the `answer` field:
- Write clear, plain English a non-lawyer can understand.
- If asked to list clauses/risks/obligations, write them as a numbered list with brief explanations — do NOT say "see JSON" or dump raw data.
- Lead with the most important point.
- Reference clause numbers where relevant (e.g. "Clause 3 states…").
- Keep under 400 words unless the question demands more.

Focus on: unlimited liability, termination ambiguity, indemnification, penalty clauses, auto-renewal traps, unfair jurisdiction.
Kenyan law: Employment Act 2007, Contract Act (Cap 23), Consumer Protection Act 2012."""

SYSTEM_SW = """Wewe ni Wakili, msaidizi wa AI wa kisheria mwenye utaalamu wa sheria za Kenya.
Una vifungu vya mkataba vilivyopatikana na historia ya mazungumzo — vitumie vyote.

Rudisha JSON halali TU — bila alama za markdown. Muundo sahihi:
{
  "answer": "<Jibu wazi na lililopangwa vizuri kwa Kiswahili rahisi. Tumia orodha namba au vichwa vya habari ndani ya kamba hii ikiwa itasaidia. USIWEKE JSON ghafi hapa.>",
  "clause_summaries": [
    {"clause_number": 1, "title": "Kichwa", "summary": "Muhtasari.", "text": "Muhtasari.", "language": "sw"}
  ],
  "risk_flags": [
    {"clause_number": 1, "type": "Dhima Isiyo na Mipaka", "risk_type": "dhima_isiyo_na_mipaka", "severity": "juu", "description": "Maelezo.", "explanation": "Maelezo.", "language": "sw"}
  ],
  "obligations": [
    {"party": "Mwajiriwa", "obligation": "Wanalazimika kufanya nini.", "condition": "Hali.", "deadline": "Tarehe.", "language": "sw"}
  ]
}

Sheria za Kenya: Sheria ya Ajira 2007, Sheria ya Mikataba (Sura 23), Sheria ya Ulinzi wa Watumiaji 2012."""

SYSTEM_KB_SUFFIX_EN = """
NOTE: Context is from the Kenyan Law Knowledge Base, not the user's document.
Answer based on general Kenyan legal principles and make this clear in your answer."""

SYSTEM_KB_SUFFIX_SW = """
KUMBUKA: Muktadha unatoka kwenye Hifadhidata ya Sheria ya Kenya, si hati ya mtumiaji.
Jibu kulingana na kanuni za jumla za kisheria na eleza hili wazi."""

# ── Document analysis prompt (upload time) ────────────────────────────────────
ANALYSE_SYSTEM_EN = "You are Wakili, a Kenyan AI legal analyst. Return ONLY valid JSON — no markdown, no extra text."
ANALYSE_SYSTEM_SW = "Wewe ni Wakili, mchanganuzi wa AI wa kisheria wa Kenya. Rudisha JSON TU — bila markdown."

ANALYSE_TEMPLATE_EN = """Analyse this contract and return ONLY this JSON — no markdown fences:
{{
  "clause_summaries": [
    {{"clause_number": 1, "title": "Clause title", "summary": "One-sentence summary.", "text": "One-sentence summary.", "language": "en"}}
  ],
  "risk_flags": [
    {{"clause_number": 1, "type": "Human-readable risk name", "risk_type": "machine_key", "severity": "low|medium|high", "description": "Plain-language explanation.", "explanation": "Plain-language explanation.", "language": "en"}}
  ],
  "obligations": [
    {{"party": "Party name", "obligation": "What they must do.", "condition": "Condition if any.", "deadline": "Deadline if any.", "language": "en"}}
  ]
}}

CONTRACT TEXT:
{text}"""

ANALYSE_TEMPLATE_SW = """Changanua mkataba huu na urudishe muundo huu wa JSON TU — bila markdown:
{{
  "clause_summaries": [
    {{"clause_number": 1, "title": "Kichwa", "summary": "Muhtasari.", "text": "Muhtasari.", "language": "sw"}}
  ],
  "risk_flags": [
    {{"clause_number": 1, "type": "Jina la hatari", "risk_type": "ufunguo", "severity": "chini|kati|juu", "description": "Maelezo.", "explanation": "Maelezo.", "language": "sw"}}
  ],
  "obligations": [
    {{"party": "Jina la chama", "obligation": "Wajibu.", "condition": "Hali.", "deadline": "Tarehe.", "language": "sw"}}
  ]
}}

MAANDISHI YA MKATABA:
{text}"""


class GroqService:
    """Singleton Groq client."""
    _instance: "GroqService | None" = None

    @classmethod
    def get_instance(cls) -> "GroqService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com "
                "and add GROQ_API_KEY=your_key to your .env file."
            )
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        log.info("Groq client initialised", model=settings.GROQ_MODEL)

    def _call(self, messages: list[dict]) -> str:
        """Send messages to Groq. Returns raw text content."""
        try:
            response = self._client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_NEW_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            log.error("Groq generation failed", error=str(e))
            return json.dumps({
                "answer": "I was unable to generate a response. Please try again.",
                "clause_summaries": [],
                "risk_flags": [],
                "obligations": [],
            })

    def parse_json(self, raw: str) -> dict:
        """Extract JSON from LLM output, handles accidental markdown fences."""
        cleaned = re.sub(r"```json|```", "", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            # Prose fallback — return raw text as the answer
            return {
                "answer": cleaned,
                "clause_summaries": [],
                "risk_flags": [],
                "obligations": [],
            }

    def _normalise_risk_flags(self, flags: list) -> list:
        """
        Mirror fields so both renderers work:
          - Document viewer ([id]/page.tsx) uses `type` + `description`
          - Chat bubble (chat/page.tsx)     uses `risk_type` + `explanation`
        """
        out = []
        for r in flags:
            r = dict(r)
            r["type"]        = r.get("type") or r.get("risk_type", "Unknown Risk")
            r["risk_type"]   = r.get("risk_type") or r.get("type", "unknown_risk")
            r["description"] = r.get("description") or r.get("explanation", "")
            r["explanation"] = r.get("explanation") or r.get("description", "")
            # Normalise severity for document viewer (English only)
            severity_map = {"juu": "high", "kati": "medium", "chini": "low"}
            r["severity"] = severity_map.get(r.get("severity", ""), r.get("severity", "medium"))
            out.append(r)
        return out

    def _normalise_clause_summaries(self, clauses: list) -> list:
        """
        Mirror `text` ↔ `summary` so both the document viewer (`c.text`)
        and any other consumer (`c.summary`) are populated.
        """
        out = []
        for c in clauses:
            c = dict(c)
            c["text"]    = c.get("text") or c.get("summary", "")
            c["summary"] = c.get("summary") or c.get("text", "")
            out.append(c)
        return out

    def ask(
        self,
        question: str,
        context: str,
        language: str,
        history: list = [],
        used_knowledge_base: bool = False,
    ) -> dict:
        """
        Full Q&A with conversation memory.
        Returns prose `answer` + structured side-data with normalised fields.
        """
        if language == "sw":
            system = SYSTEM_SW + (SYSTEM_KB_SUFFIX_SW if used_knowledge_base else "")
            disclaimer = DISCLAIMER_SW
        else:
            system = SYSTEM_EN + (SYSTEM_KB_SUFFIX_EN if used_knowledge_base else "")
            disclaimer = DISCLAIMER_EN

        messages = [{"role": "system", "content": system}]

        # Inject history (capped to avoid token blowout)
        for turn in history[-(settings.MAX_HISTORY_TURNS):]:
            messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append({
            "role": "user",
            "content": (
                f"CONTEXT (retrieved contract clauses):\n{context}\n\n"
                f"USER QUESTION:\n{question}\n\n"
                "Write a clear prose answer in the `answer` field. "
                "Populate clause_summaries, risk_flags, and obligations only "
                "when directly relevant to this question.\n\n"
                "JSON RESPONSE:"
            ),
        })

        raw = self._call(messages)
        result = self.parse_json(raw)

        result["risk_flags"]       = self._normalise_risk_flags(result.get("risk_flags", []))
        result["clause_summaries"] = self._normalise_clause_summaries(result.get("clause_summaries", []))

        if result.get("answer"):
            result["answer"] = result["answer"].strip() + disclaimer

        return result

    def analyse(self, text: str, language: str) -> dict:
        """
        Document analysis at upload time.
        Returns structured JSON for storage — clause summaries, risk flags, obligations.
        """
        if language == "sw":
            system = ANALYSE_SYSTEM_SW
            user_msg = ANALYSE_TEMPLATE_SW.format(text=text[:3000])
        else:
            system = ANALYSE_SYSTEM_EN
            user_msg = ANALYSE_TEMPLATE_EN.format(text=text[:3000])

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]
        raw = self._call(messages)
        result = self.parse_json(raw)

        result["risk_flags"]       = self._normalise_risk_flags(result.get("risk_flags", []))
        result["clause_summaries"] = self._normalise_clause_summaries(result.get("clause_summaries", []))

        return result


# Lazy singleton accessor
_instance: GroqService | None = None


def get_groq_service() -> GroqService:
    global _instance
    if _instance is None:
        _instance = GroqService()
    return _instance


groq_service = None  # resolved lazily via get_groq_service()