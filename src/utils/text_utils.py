"""
MedGuard - Text Cleaning and Candidate Extraction Utilities
Filters pharmaceutical packaging noise (batch numbers, expiry dates, dosages, manufacturers)
from raw OCR output before normalization.
"""
import re
from typing import Optional

from config.settings import MIN_TOKEN_LENGTH

# Regex patterns for stripping packaging metadata
BATCH_PATTERN = re.compile(
    r"\b(b\.?no\.?|batch\s*(?:no\.?|#)?|lot\s*(?:no\.?|#)?)\s*[:\-]?\s*[\w\d\-]+",
    re.IGNORECASE,
)

EXPIRY_MFG_PATTERN = re.compile(
    r"\b(exp(?:\.|iry)?(?:\s*date)?|mfg(?:\.|r)?(?:\s*date)?|mfd\.?|use\s*before)\s*[:\-]?\s*[\w\d\/\.\-]+",
    re.IGNORECASE,
)

DATE_FORMAT_PATTERN = re.compile(
    r"\b\d{1,2}[\/\-\.]\d{2,4}\b",
    re.IGNORECASE,
)

DOSAGE_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|%|w\/w|w\/v|v\/v)\b",
    re.IGNORECASE,
)

PHARMA_FORM_PATTERN = re.compile(
    r"\b(tablets?|capsules?|cap|tab|syrup|injection|suspension|drops?|cream|ointment|gel|solution|elixir|ip|bp|usp)\b",
    re.IGNORECASE,
)

MANUFACTURER_NOISE_PATTERN = re.compile(
    r"\b(pvt\.?\s*ltd\.?|limited|ltd\.?|laboratories|pharma(?:ceuticals)?|mfg\.?\s*lic\.?\s*(?:no\.?)?|licence\s*no\.?|store\s*below|keep\s*out\s*of\s*reach|for\s*external\s*use|schedule\s*[hgh1]\s*drug)\b",
    re.IGNORECASE,
)

PUNCTUATION_PATTERN = re.compile(r"[^\w\s\-]")


def normalize_whitespace(text: str) -> str:
    """Collapses consecutive spaces, tabs, and newlines into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def normalize_case(text: str) -> str:
    """Converts string to lowercase."""
    return text.lower().strip()


def remove_packaging_noise(text: str) -> str:
    """
    Strips out pharmaceutical packaging noise:
    batch numbers, expiry dates, dosage units, formulation types, and manufacturer tags.
    """
    cleaned = BATCH_PATTERN.sub(" ", text)
    cleaned = EXPIRY_MFG_PATTERN.sub(" ", cleaned)
    cleaned = DATE_FORMAT_PATTERN.sub(" ", cleaned)
    cleaned = DOSAGE_PATTERN.sub(" ", cleaned)
    cleaned = PHARMA_FORM_PATTERN.sub(" ", cleaned)
    cleaned = MANUFACTURER_NOISE_PATTERN.sub(" ", cleaned)
    return normalize_whitespace(cleaned)


def clean_ocr_text(raw_text: str) -> str:
    """
    Complete text cleaning pipeline for raw OCR output:
    1. Normalizes case to lowercase.
    2. Strips packaging noise regexes.
    3. Cleans stray punctuation.
    4. Normalizes whitespace.
    """
    if not raw_text:
        return ""

    lowered = normalize_case(raw_text)
    noise_stripped = remove_packaging_noise(lowered)
    punct_cleaned = PUNCTUATION_PATTERN.sub(" ", noise_stripped)
    return normalize_whitespace(punct_cleaned)


def extract_candidate_tokens(cleaned_text: str) -> list[str]:
    """
    Extracts candidate medicine name tokens (individual words and 2-word combinations)
    for dictionary lookup and fuzzy matching.
    Filters out numeric-only tokens and tokens shorter than MIN_TOKEN_LENGTH.
    """
    if not cleaned_text:
        return []

    words = [
        w for w in cleaned_text.split()
        if len(w) >= MIN_TOKEN_LENGTH and not w.isdigit()
    ]

    candidates: list[str] = []

    # 1. Full cleaned string (if short enough to be a brand phrase)
    if cleaned_text and not cleaned_text.isdigit() and len(cleaned_text) >= MIN_TOKEN_LENGTH:
        candidates.append(cleaned_text)

    # 2. Bigrams (e.g. "bayer aspirin", "dolo 650" -> "dolo paracetamol")
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        if bigram not in candidates:
            candidates.append(bigram)

    # 3. Unigrams
    for word in words:
        if word not in candidates:
            candidates.append(word)

    return candidates
