import re


def fix_encoding(text: str) -> str:
    """
    Fix common mojibake caused by incorrect UTF-8 decoding and
    common government PDF font encoding artifacts.
    """
    try:
        repaired = text.encode("latin1").decode("utf-8")

        bad_patterns = ["â", "Â", "ð", ""]
        original_bad = sum(text.count(pattern) for pattern in bad_patterns)
        repaired_bad = sum(repaired.count(pattern) for pattern in bad_patterns)

        if repaired_bad < original_bad:
            text = repaired
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    # Replace common PDF font extraction artifacts
    replacements = {
        "?T": "'",
        "?Ts": "'s",
        "?T": "'",
        "?Ts": "'s",
        "?o": '"',
        "?o": '"',
        "??": '"',
        "??": '"',
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€“": "-",
        "â€”": "-",
        "\x00": " ",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    return text


def clean_text(text: str) -> str:
    """
    Clean extracted PDF/document text by:
    - fixing encoding artifacts
    - removing excessive whitespace
    - normalizing line breaks
    - removing spaces at line boundaries
    """
    text = fix_encoding(text)

    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    text = "\n".join(lines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()