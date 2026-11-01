import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.nlp.llm_service import LLMService


service = LLMService()


question = "How much financial assistance does PM-KISAN provide?"

context = """
Under PM-KISAN, the financial benefit of Rs.6000/- per year
is released to eligible farmers in three installments of
Rs.2000/- each.
"""


answer = service.generate_answer(
    question=question,
    context=context,
)


print("\nQuestion:")
print(question)

print("\nAnswer:")
print(answer)