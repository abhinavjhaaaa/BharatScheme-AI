import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.documents.text_cleaner import clean_text


sample_text = """
1


PRADHAN MANTRI KISAN SAMMAN NIDHI SCHEME


(PM-KISAN SCHEME)


OPERATIONAL GUIDELINES
"""


cleaned = clean_text(sample_text)

print("Original:")
print(sample_text)

print("\nCleaned:")
print(cleaned)