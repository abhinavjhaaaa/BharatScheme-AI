import logging
import re
from typing import Optional, List, Dict, Any

import ollama

from backend.app.core.config import settings
from backend.app.services.retrieval.faiss_search import FAISSSearch

logger = logging.getLogger(__name__)

# Common Hinglish words used in Indian scheme queries
HINGLISH_WORDS = {
    "kya", "kaise", "kitna", "kitne", "kitni", "kab", "kahan", "kaun",
    "kisko", "kise", "kinhe", "mujhe", "mera", "meri", "mere", "chahiye",
    "milega", "milta", "milte", "milenge", "paane", "prapt", "yojana",
    "yojna", "labh", "fayda", "fayde", "aavedan", "patra", "patrata",
    "yogyata", "kyu", "kyon", "liye", "batao", "bataiye", "samjhao",
    "paisa", "paise", "rupaye", "rupee", "kisan", "kisano", "chhatravritti",
    "padhai", "dastavez", "kagaz", "shiksha", "sahayata", "kare", "karna",
    "sakta", "sakti", "sakte", "hai", "hain", "bhi", "nahi", "nahin",
    "hoga", "hogi", "honge", "bhare", "bharo", "jankari",
    "kisme", "isme", "usme", "ghar", "awas", "bima", "pension"
}

# Hinglish semantic keyword mapping to English document search terms
HINGLISH_MAPPINGS = [
    (r"\b(paisa|paise|rupaye|rupee|dhanrashi|rashi|kist|installment|installments)\b", "financial assistance amount money installments DBT"),
    (r"\b(kitna|kitne|kitni)\b", "how much financial assistance amount"),
    (r"\b(patra|patrata|yogyata|kaun|kisko|kise|kinhe|apply kar|eligibility)\b", "eligibility criteria requirements who can apply"),
    (r"\b(fayda|fayde|labh|suvidha|benefit|benefits)\b", "benefits financial assistance support"),
    (r"\b(aavedan|kaise kare|kaise apply|kahan kare|form|registration)\b", "how to apply application process registration official portal"),
    (r"\b(kagaz|dastavez|document|documents|praman patra)\b", "documents required checklist certificates"),
    (r"\b(kisan|kisano|kheti|khet|zameen)\b", "PM-KISAN farmer cultivable landholding"),
    (r"\b(chhatravritti|scholarship|scholarships|padhai|college|university|student|vidyarthi)\b", "scholarship PM-USP CSSS AICTE Swanath technical student"),
    (r"\b(technical|degree|diploma|engineering)\b", "AICTE Swanath technical degree diploma"),
    (r"\b(anarth|orphan|covid|shaheed|martyred)\b", "orphan covid deceased martyred armed forces Swanath"),
    (r"\b(yojana|yojna|scheme)\b", "government scheme"),
    (r"\b(swasthya|health|ilaj|hospital)\b", "PM-JAY Ayushman Bharat health insurance"),
    (r"\b(awas|ghar|makaan)\b", "PMAY Pradhan Mantri Awas Yojana housing"),
    (r"\b(pension|budhapa)\b", "Atal Pension Yojana APY"),
]

# Hindi (Devanagari) semantic keyword mapping for hybrid search
HINDI_MAPPINGS = [
    (r"(किसान|खेती|जमीन)", "PM-KISAN farmer agriculture landholding"),
    (r"(छात्रवृत्ति|स्कॉलरशिप|पढ़ाई|कॉलेज|विश्वविद्यालय|विद्यार्थी)", "scholarship PM-USP CSSS AICTE Swanath student"),
    (r"(पैसे|रुपये|राशि|किस्त|सहायता)", "financial assistance amount Rs installments DBT"),
    (r"(पात्रता|पात्र|योग्यता|नियम|शर्तें)", "eligibility criteria requirements"),
    (r"(लाभ|फायदे|सुविधाएं)", "benefits financial assistance"),
    (r"(आवेदन|फॉर्म|पंजीकरण|कैसे करें)", "how to apply application process portal"),
    (r"(दस्तावेज|कागजात|प्रमाण पत्र)", "documents required checklist"),
    (r"(तकनीकी|डिग्री|डिप्लोमा)", "technical degree diploma AICTE Swanath"),
    (r"(अनाथ|कोविड|शहीद)", "orphan covid martyred armed forces Swanath"),
    (r"(योजना|सरकारी)", "government scheme"),
]

KNOWN_SCHEMES_KEYWORDS = [
    ("PM-USP-CSSS", ["scholarship", "scholarships", "csss", "pm-usp", "college", "university", "chhatravritti"]),
    ("AICTE-SWANATH-TECHNICAL", ["swanath", "aicte", "technical degree", "engineering diploma"]),
    ("PM-KISAN", ["kisan", "farmer", "agriculture", "kheti", "zameen", "landholding"]),
    ("PM-JAY", ["ayushman", "pm-jay", "health insurance", "hospital", "swasthya", "bima"]),
    ("PMAY-G", ["awas", "housing", "pmay", "ghar", "makaan"]),
    ("SSY", ["sukanya", "ssy", "beti", "girl child savings"]),
    ("PMJDY", ["jan dhan", "pmjdy", "bank account", "zero balance"]),
    ("PMMY", ["mudra", "pmmy", "business loan", "shishu", "kishore", "tarun"]),
    ("APY", ["atal pension", "apy", "pension", "monthly pension"]),
    ("PM-VISHWAKARMA", ["vishwakarma", "artisan", "craftsman", "karigar"]),
    ("PMJJBY", ["jeevan jyoti", "pmjjby", "life insurance"]),
    ("PMSBY", ["suraksha bima", "pmsby", "accidental insurance"]),
    ("PMUY", ["ujjwala", "pmuy", "lpg", "gas connection"]),
]


def detect_language(text: str) -> str:
    """
    Detect whether the input question is in:
    - 'hi': Hindi (written in Devanagari script)
    - 'hinglish': Hinglish (Hindi written in Roman/English alphabet)
    - 'en': English (default)
    """
    if not text:
        return "en"

    # Check for Devanagari characters (U+0900 to U+097F)
    if any("\u0900" <= ch <= "\u097F" for ch in text):
        return "hi"

    # Check for Romanized Hindi (Hinglish) tokens
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    if tokens & HINGLISH_WORDS:
        return "hinglish"

    return "en"


def correct_typos(text: str) -> str:
    """Correct common spelling mistakes and variations."""
    q_lower = text.lower()
    typo_map = {
        r"\belegiblity\b": "eligibility",
        r"\belegibility\b": "eligibility",
        r"\beligiblity\b": "eligibility",
        r"\belegible\b": "eligible",
        r"\beligibal\b": "eligible",
        r"\bscolarship\b": "scholarship",
        r"\bscolarships\b": "scholarships",
        r"\bscholarhip\b": "scholarship",
        r"\bscholarhips\b": "scholarships",
        r"\bfamrer\b": "farmer",
        r"\bfarmar\b": "farmer",
        r"\bbenifit\b": "benefit",
        r"\bbenifits\b": "benefits",
        r"\byojna\b": "yojana",
        r"\bdastabez\b": "dastavez",
        r"\bdastavej\b": "dastavez",
        r"\baavedan\b": "aavedan",
    }
    for pattern, replacement in typo_map.items():
        q_lower = re.sub(pattern, replacement, q_lower)
    return q_lower


class RAGService:
    """
    Multilingual Retrieval-Augmented Generation (RAG) Service.

    Supports:
    - English (en)
    - Hindi in Devanagari script (hi)
    - Hinglish in Roman script (hinglish)

    Retrieves relevant government document chunks from FAISS across
    all indexed schemes and uses local Ollama (Qwen2.5-3B-Instruct)
    to generate grounded, hallucination-resistant answers with verified citations
    in the user's preferred language.
    """

    def __init__(
        self,
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
        model: str = settings.ollama_model,
        base_url: str = settings.ollama_base_url,
        similarity_threshold: float = settings.similarity_threshold,
    ):
        self.index_path = str(index_path or settings.default_faiss_index)
        self.metadata_path = str(metadata_path or settings.default_faiss_metadata)
        self.model = model
        self.base_url = base_url
        self.similarity_threshold = similarity_threshold

        self.searcher = FAISSSearch(
            index_path=self.index_path,
            metadata_path=self.metadata_path,
        )
        self.client = ollama.Client(host=self.base_url)

    def _extract_recent_scheme(self, history: Optional[List[Dict[str, Any]]]) -> Optional[str]:
        """Inspect recent conversation messages to identify the active scheme context."""
        if not history:
            return None
        for msg in reversed(history[-4:]):
            content = str(msg.get("content", "")).lower()
            for scheme_id, keywords in KNOWN_SCHEMES_KEYWORDS:
                if any(kw in content for kw in keywords):
                    return scheme_id
        return None

    def _build_search_query(self, query: str, lang: str, context_scheme: Optional[str] = None) -> str:
        """
        Transform/expand query so that FAISS semantic search maps
        Hindi, Hinglish, and short telegraphic queries accurately to English government documents.
        """
        q = query.strip()
        q_norm = correct_typos(q)

        additions = []
        if context_scheme:
            additions.append(context_scheme.replace("-", " "))

        if lang == "hinglish":
            for pattern, english_terms in HINGLISH_MAPPINGS:
                if re.search(pattern, q_norm):
                    additions.append(english_terms)
            return f"{q_norm} {' '.join(additions)}".strip()

        elif lang == "hi":
            for pattern, english_terms in HINDI_MAPPINGS:
                if re.search(pattern, q):
                    additions.append(english_terms)
            return f"{q} {' '.join(additions)}".strip()

        else:
            # English short query handling
            words = q_norm.split()
            if len(words) <= 3:
                if "benefit" in q_norm or "fayde" in q_norm:
                    additions.append("benefits financial assistance support amount")
                elif "eligib" in q_norm or "patra" in q_norm:
                    additions.append("eligibility criteria requirements conditions who can apply")
                elif "scholarship" in q_norm:
                    additions.append("scholarship amounts eligibility college technical degree students PM-USP AICTE Swanath")
                elif "farmer" in q_norm or "kisan" in q_norm:
                    additions.append("PM-KISAN financial benefit Rs 6000 rules cultivable landholding")
                elif "document" in q_norm or "kagaz" in q_norm:
                    additions.append("documents required checklist Aadhaar bank account certificate")
                elif "apply" in q_norm or "registration" in q_norm:
                    additions.append("how to apply application process registration official portal")

            return f"{q_norm} {' '.join(additions)}".strip()

    def _clarify_question(self, question: str, lang: str, context_scheme: Optional[str] = None) -> str:
        """
        Produce a clear, complete question prompt for the LLM
        so single-word or telegraphic user inputs (e.g. 'benefits', 'elegiblity', 'documents')
        are answered fully and comprehensively based on the context.
        """
        q_clean = correct_typos(question).strip()
        words = q_clean.split()
        scheme_mention = f" for {context_scheme}" if context_scheme else ""

        # Only transform if query is brief (<= 3 words)
        if len(words) <= 3:
            if any(k in q_clean for k in ["eligib", "patrata", "yogyata", "paatr"]):
                if lang == "hi":
                    return f"इस योजना{scheme_mention} के लिए कौन पात्र है और क्या पात्रता शर्तें, आय सीमा व नियम हैं?"
                elif lang == "hinglish":
                    return f"Is scheme{scheme_mention} ke liye kaun eligible hai aur kya eligibility criteria, income limit aur rules hain?"
                else:
                    return f"What are the eligibility criteria, income limits, and qualifying requirements{scheme_mention}?"

            if any(k in q_clean for k in ["benefit", "fayda", "fayde", "labh"]):
                if lang == "hi":
                    return f"इस योजना{scheme_mention} के अंतर्गत क्या-क्या लाभ, वित्तीय सहायता और सुविधाएं दी जाती हैं?"
                elif lang == "hinglish":
                    return f"Is scheme{scheme_mention} ke antargat kya financial assistance, kist aur fayde milte hain?"
                else:
                    return f"What are the financial benefits, assistance amounts, and support provided{scheme_mention}?"

            if any(k in q_clean for k in ["document", "kagaz", "dastavez"]):
                if lang == "hi":
                    return f"इस योजना{scheme_mention} के लिए कौन-से आवश्यक दस्तावेज और प्रमाण पत्र चाहिए?"
                elif lang == "hinglish":
                    return f"Is scheme{scheme_mention} ke liye kaun-se zaroori documents aur certificates chahiye?"
                else:
                    return f"What are the mandatory documents and certificates required to apply{scheme_mention}?"

            if any(k in q_clean for k in ["apply", "aavedan", "kaise kare"]):
                if lang == "hi":
                    return f"इस योजना{scheme_mention} के लिए आवेदन और पंजीकरण कैसे करें?"
                elif lang == "hinglish":
                    return f"Is scheme{scheme_mention} ke liye official portal par aavedan kaise karein?"
                else:
                    return f"What is the step-by-step application and registration process{scheme_mention}?"

            if any(k in q_clean for k in ["scholarship", "chhatravritti"]):
                if lang == "hi":
                    return "छात्रवृत्ति योजनाओं (जैसे PM-USP CSSS और AICTE Swanath) में प्रति वर्ष कितनी राशि और क्या सहायता मिलती है?"
                elif lang == "hinglish":
                    return "Scholarship schemes (jaise PM-USP CSSS aur AICTE Swanath) me per year kitna paisa aur sahayata milti hai?"
                else:
                    return "How much financial assistance and scholarship amounts are provided under student scholarship schemes?"

        return question.strip()

    def answer(
        self,
        question: str,
        top_k: int = 5,
        scheme_id: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> dict:
        """
        Answer a question with grounded retrieval and source citations
        in English, Hindi, or Hinglish based on the user's input language.
        """
        cleaned_question = question.strip() if question else ""
        detected_language = detect_language(cleaned_question)

        if not cleaned_question:
            no_q_msgs = {
                "hi": "कृपया किसी भारतीय सरकारी योजना के बारे में प्रश्न पूछें।",
                "hinglish": "Kripya kisi Indian government scheme ke bare me sawal puchein.",
                "en": "Please ask a question about an Indian government scheme."
            }
            return {
                "answer": no_q_msgs.get(detected_language, no_q_msgs["en"]),
                "sources": [],
                "confidence": "low",
                "is_grounded": False,
                "detected_language": detected_language,
            }

        # Determine context scheme from explicit argument or prior conversation history
        context_scheme = scheme_id or self._extract_recent_scheme(history)

        # 1. Transform query for semantic FAISS search
        search_query = self._build_search_query(cleaned_question, detected_language, context_scheme)

        # 2. Retrieve top matching chunks from FAISS index
        try:
            results = self.searcher.search(
                query=search_query,
                top_k=top_k,
                scheme_id=scheme_id,
            )
        except Exception as e:
            logger.error(f"Search retrieval error: {e}")
            results = []

        if not results:
            not_found_msgs = {
                "hi": "मुझे उपलब्ध आधिकारिक सरकारी दस्तावेजों में आपके प्रश्न से संबंधित जानकारी नहीं मिली।",
                "hinglish": "Mujhe available official government documents me aapke sawal se related jankari nahi mili.",
                "en": "I could not find relevant information in the available government documents for your query."
            }
            return {
                "answer": not_found_msgs.get(detected_language, not_found_msgs["en"]),
                "sources": [],
                "confidence": "low",
                "is_grounded": False,
                "detected_language": detected_language,
            }

        # 3. Check maximum similarity score against threshold to block hallucinations
        max_score = max(r["similarity_score"] for r in results)

        # Adaptive threshold: recognized scheme/welfare terms use 0.22, out-of-domain use 0.35
        scheme_keywords = [
            "scheme", "scholarship", "kisan", "farmer", "benefit", "eligib",
            "amount", "money", "aicte", "swanath", "csss", "pm-usp", "pm-kisan",
            "college", "university", "document", "apply", "ayushman", "awas",
            "pension", "bima", "yojana", "yojna", "paisa", "paise", "rupaye",
            "labh", "fayde", "fayda", "patra", "patrata", "aavedan", "dastavez",
            "kagaz", "kisko", "kitna", "kitne", "milega", "योजना", "किसान",
            "छात्रवृत्ति", "पैसे", "रुपये", "पात्रता", "लाभ", "आवेदन", "दस्तावेज"
        ]
        q_lower = cleaned_question.lower()
        is_scheme_query = (
            any(k in q_lower for k in scheme_keywords)
            or any(k in search_query.lower() for k in scheme_keywords)
            or context_scheme is not None
        )
        effective_threshold = 0.22 if is_scheme_query else self.similarity_threshold

        if max_score < effective_threshold:
            rejection_msgs = {
                "hi": (
                    "मुझे उपलब्ध आधिकारिक सरकारी दस्तावेजों में इस विषय पर पर्याप्त जानकारी नहीं मिली। "
                    "यह प्रणाली केवल सत्यापित सरकारी दिशानिर्देशों पर आधारित तथ्यपूर्ण उत्तर देती है। "
                    "कृपया योजना का नाम जांचें या अपना प्रश्न पुनः लिखें।"
                ),
                "hinglish": (
                    "Mujhe available official government documents me is bare me jankari nahi mili. "
                    "Yeh system sirf verified government guidelines ke aadhar par sahi jankari deta hai. "
                    "Kripya scheme ka naam check karein ya apna sawal dobara likhein."
                ),
                "en": (
                    "I could not find sufficient information about this in the available official government documents. "
                    "The system only answers questions grounded in verified government guidelines. "
                    "Please check the scheme name or rephrase your question."
                )
            }
            return {
                "answer": rejection_msgs.get(detected_language, rejection_msgs["en"]),
                "sources": [],
                "confidence": "low",
                "is_grounded": False,
                "detected_language": detected_language,
            }

        # Keep relevant chunks
        filtered_results = [
            r for r in results if r["similarity_score"] >= max(effective_threshold, max_score - 0.25)
        ]
        if not filtered_results:
            filtered_results = results[:2]

        # 4. Build grounded context with explicit citations
        context_blocks = []
        for r in filtered_results:
            block = (
                f"[Source Document: {r.get('source_file', 'Official Guidelines')}, "
                f"Page {r.get('page_number', 'N/A')}, Scheme: {r.get('scheme_id', 'General')}]\n"
                f"{r.get('text', '').strip()}"
            )
            context_blocks.append(block)

        context = "\n\n---\n\n".join(context_blocks)

        # Clarify telegraphic user questions for LLM prompt
        prompt_question = self._clarify_question(cleaned_question, detected_language, context_scheme)

        # 5. Formulate language-specific system prompt
        if detected_language == "hi":
            system_prompt = (
                "You are BharatScheme AI (भारत स्कीम एआई), an official assistant for Indian government schemes.\n"
                "LANGUAGE RULE: You must answer STRICTLY in Hindi using Devanagari script (हिन्दी).\n"
                "Keep the tone respectful, clear, and easy to understand for citizens.\n\n"
                "STRICT RULES:\n"
                "1. Answer using the provided official context excerpts. Never invent facts.\n"
                "2. State key figures, amounts (जैसे ₹6,000 प्रति वर्ष, ₹2,000 की 3 किस्तें, ₹12,000, ₹20,000, ₹50,000), dates, and eligibility limits accurately.\n"
                "3. Mention the relevant source document and page number in your answer.\n"
                "4. If the context does not contain the answer, say clearly: "
                "'उपलब्ध आधिकारिक सरकारी दस्तावेजों में इस विषय पर जानकारी उपलब्ध नहीं है।'"
            )
        elif detected_language == "hinglish":
            system_prompt = (
                "You are BharatScheme AI, an official assistant for Indian government schemes.\n"
                "LANGUAGE RULE: You must answer STRICTLY in Hinglish (Hindi written using English/Roman alphabet, simple everyday conversational style).\n"
                "CRITICAL: Do NOT use Devanagari script. Use English letters to write Hindi.\n"
                "Example Hinglish style:\n"
                "\"PM-KISAN scheme ke tahat eligible kisano ko har saal Rs. 6,000 ki financial assistance milti hai, jo 3 installments me Rs. 2,000 karke direct bank account me aati hai.\"\n\n"
                "STRICT RULES:\n"
                "1. Answer using the provided official context excerpts. Never invent facts.\n"
                "2. State exact amounts, installments, income limits, and eligibility conditions clearly in Hinglish.\n"
                "3. Mention the source document and page number.\n"
                "4. If the context does not contain the answer, say clearly: "
                "'Available official government documents me is bare me jankari nahi hai.'"
            )
        else:
            system_prompt = (
                "You are BharatScheme AI, an official and factual assistant for Indian government schemes.\n"
                "LANGUAGE RULE: Answer in English.\n"
                "Answer the user's question using the provided official context excerpts.\n\n"
                "STRICT RULES:\n"
                "1. Answer strictly based on the provided context. Never invent or assume facts.\n"
                "2. State key figures, amounts (e.g. ₹6,000/year, ₹12,000/year, ₹20,000/year, ₹50,000/year), dates, and eligibility limits accurately.\n"
                "3. Mention the relevant source and page/section number when stating specific facts.\n"
                "4. If the context does not contain the answer, say clearly: "
                "'The available official government documents do not provide information on this topic.'\n"
                "5. Keep the explanation concise, professional, and easy to read."
            )

        user_prompt = f"""Official Government Document Context:
{context}

User Question:
{prompt_question}

Grounded Answer:"""

        # 6. Call local Ollama LLM
        answer_text = None
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                options={
                    "temperature": 0.2,
                },
            )
            raw_answer = response["message"]["content"].strip()
            # If Ollama responded with not found phrase but we have high similarity chunks, verify
            if "do not provide information" not in raw_answer.lower() or max_score < 0.40:
                answer_text = raw_answer
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")

        # Fallback if Ollama is not accessible or returned false negative on high-confidence chunk
        if not answer_text:
            top_chunk = filtered_results[0]
            answer_text = (
                f"Source: {top_chunk.get('source_file')} (Page {top_chunk.get('page_number')}):\n\n"
                f"{top_chunk.get('text')[:350]}..."
            )

        # 7. Format structured sources
        confidence = "high" if max_score >= 0.48 else "medium"

        sources = []
        seen = set()
        for r in filtered_results:
            key = (r.get("source_file"), r.get("page_number"))
            if key in seen:
                continue
            seen.add(key)
            snippet = r.get("text", "").replace("\n", " ")
            if len(snippet) > 220:
                snippet = snippet[:220].rsplit(" ", 1)[0] + "..."

            sources.append(
                {
                    "scheme_id": r.get("scheme_id", ""),
                    "source_file": r.get("source_file", ""),
                    "page_number": r.get("page_number", 1),
                    "chunk_id": r.get("chunk_id", ""),
                    "similarity_score": r.get("similarity_score", 0.0),
                    "snippet": snippet,
                }
            )

        return {
            "answer": answer_text,
            "sources": sources,
            "confidence": confidence,
            "is_grounded": True,
            "detected_language": detected_language,
        }
