import logging
import re
import ollama
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

HINGLISH_WORDS = {
    "kya", "kaise", "kitna", "kitne", "kitni", "kab", "kahan", "kaun",
    "kisko", "kise", "mujhe", "mera", "meri", "mere", "chahiye", "milega",
    "milta", "milte", "milenge", "yojana", "yojna", "labh", "fayda", "fayde",
    "aavedan", "patra", "patrata", "paisa", "paise", "rupaye", "kisan",
    "chhatravritti", "padhai", "dastavez", "kagaz", "hai", "hain", "kare"
}


def detect_language(text: str) -> str:
    if not text:
        return "en"
    if any("\u0900" <= ch <= "\u097F" for ch in text):
        return "hi"
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    if tokens & HINGLISH_WORDS:
        return "hinglish"
    return "en"


class LLMService:
    """
    Service for generating grounded answers using local Ollama (Qwen2.5-3B-Instruct).
    Supports English, Hindi, and Hinglish.
    """

    def __init__(
        self,
        model: str = settings.ollama_model,
        base_url: str = settings.ollama_base_url,
    ):
        self.model = model
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)

    def generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Generate a strictly grounded answer from document context in the user's language.
        """
        lang = detect_language(question)

        if lang == "hi":
            system_prompt = """You are BharatScheme AI (भारत स्कीम एआई), an official assistant for Indian government schemes.
Answer strictly in Hindi using Devanagari script (हिन्दी).
Rules:
1. Answer ONLY using the provided government document context.
2. If the context does not contain enough information, state:
   "उपलब्ध आधिकारिक सरकारी दस्तावेजों में इस विषय पर पर्याप्त जानकारी नहीं मिली।"
3. Mention key numbers, amounts, and eligibility requirements accurately.
4. Keep the tone respectful, clear, and helpful."""
        elif lang == "hinglish":
            system_prompt = """You are BharatScheme AI, an official assistant for Indian government schemes.
Answer strictly in Hinglish (Hindi written using English/Roman alphabet, e.g. "PM-KISAN scheme me eligible kisano ko har saal Rs. 6,000 ki financial assistance milti hai...").
Do NOT use Devanagari script.
Rules:
1. Answer ONLY using the provided government document context.
2. If the context does not contain enough information, state:
   "Available official documents me is bare me jankari nahi mili."
3. Mention key numbers, amounts, and eligibility requirements accurately.
4. Keep the tone conversational, clear, and helpful."""
        else:
            system_prompt = """You are BharatScheme AI, an official and precise government scheme assistant.
Your duty is to answer questions about Indian government schemes accurately and concisely in English.
Rules:
1. Answer ONLY using the provided government document context.
2. If the context does not contain enough information to answer the question, state:
   "I could not find sufficient information about this in the available official government documents."
3. Never fabricate or extrapolate facts, amounts, eligibility rules, or dates.
4. Mention key numbers, eligibility requirements, or amounts clearly when they appear in the context.
5. Keep your tone professional, neutral, and helpful."""

        user_prompt = f"""Official Government Document Context:
{context}

User Question:
{question}

Provide an accurate, grounded answer based strictly on the context above:"""

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
            return response["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(
                f"Failed to communicate with local Ollama service at {self.base_url}. "
                f"Please ensure Ollama is running (`ollama serve`). Details: {e}"
            )
