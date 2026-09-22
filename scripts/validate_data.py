"""
MedGuard - Dataset Validation Script
Validates syntax, schema, uniqueness, and consistency of local JSON datasets.
"""
import json
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import BRAND_GENERIC_MAP_FILE, INTERACTIONS_FILE


def validate_brand_generic_map() -> tuple[bool, list[str], int]:
    errors = []
    if not BRAND_GENERIC_MAP_FILE.exists():
        return False, [f"File not found: {BRAND_GENERIC_MAP_FILE}"], 0

    try:
        with open(BRAND_GENERIC_MAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"JSON syntax error in brand_generic_map.json: {e}"], 0

    if not isinstance(data, dict):
        return False, ["brand_generic_map.json root must be a JSON object (dict)"], 0

    valid_count = 0
    for brand, generic in data.items():
        if not isinstance(brand, str) or not brand.strip():
            errors.append(f"Invalid brand key: {brand!r}")
        if not isinstance(generic, str) or not generic.strip():
            errors.append(f"Invalid generic value for brand '{brand}': {generic!r}")
        if brand.strip() != brand.lower():
            errors.append(f"Brand key '{brand}' must be lowercase")
        if generic.strip() != generic.lower():
            errors.append(f"Generic value '{generic}' for brand '{brand}' must be lowercase")
        valid_count += 1

    return len(errors) == 0, errors, valid_count


def validate_interactions() -> tuple[bool, list[str], int]:
    errors = []
    if not INTERACTIONS_FILE.exists():
        return False, [f"File not found: {INTERACTIONS_FILE}"], 0

    try:
        with open(INTERACTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"JSON syntax error in interactions.json: {e}"], 0

    if not isinstance(data, list):
        return False, ["interactions.json root must be a JSON array (list)"], 0

    required_keys = {"drug_a", "drug_b", "severity", "mechanism", "plain_language", "source"}
    valid_severities = {"high", "moderate", "low"}
    seen_pairs = set()

    for idx, item in enumerate(data):
        record_id = f"Record #{idx + 1}"
        if not isinstance(item, dict):
            errors.append(f"{record_id} is not a valid JSON object")
            continue

        missing = required_keys - set(item.keys())
        if missing:
            errors.append(f"{record_id} missing required keys: {', '.join(missing)}")
            continue

        drug_a = item.get("drug_a", "").strip().lower()
        drug_b = item.get("drug_b", "").strip().lower()
        severity = item.get("severity", "").strip().lower()
        mechanism = item.get("mechanism", "").strip()
        plain = item.get("plain_language", "").strip()
        source = item.get("source", "").strip()

        if not drug_a or not drug_b:
            errors.append(f"{record_id}: drug_a and drug_b must be non-empty")
        if drug_a == drug_b:
            errors.append(f"{record_id}: drug_a and drug_b cannot be identical ('{drug_a}')")

        if severity not in valid_severities:
            errors.append(f"{record_id}: invalid severity '{severity}', must be one of {valid_severities}")

        if not mechanism or len(mechanism) < 10:
            errors.append(f"{record_id}: mechanism is too brief or empty")

        if not plain or len(plain) < 15:
            errors.append(f"{record_id}: plain_language explanation is too brief or empty")

        if not source or len(source) < 5:
            errors.append(f"{record_id}: source is missing or invalid")

        # Bidirectional uniqueness check
        pair_key = tuple(sorted([drug_a, drug_b]))
        if pair_key in seen_pairs:
            errors.append(f"{record_id}: Duplicate interaction pair detected for {pair_key}")
        else:
            seen_pairs.add(pair_key)

    return len(errors) == 0, errors, len(seen_pairs)


def run_validation():
    print("=" * 65)
    print("MedGuard: Validating Local Datasets")
    print("=" * 65)

    # 1. Brand Generic Map
    bg_valid, bg_errors, bg_count = validate_brand_generic_map()
    if bg_valid:
        print(f"[PASS] brand_generic_map.json: {bg_count} valid brand-to-generic mappings.")
    else:
        print(f"[FAIL] brand_generic_map.json encountered {len(bg_errors)} errors:")
        for err in bg_errors[:10]:
            print(f"       - {err}")

    # 2. Interactions
    int_valid, int_errors, int_count = validate_interactions()
    if int_valid:
        print(f"[PASS] interactions.json: {int_count} unique, verified interaction pairs.")
    else:
        print(f"[FAIL] interactions.json encountered {len(int_errors)} errors:")
        for err in int_errors[:10]:
            print(f"       - {err}")

    print("-" * 65)
    if bg_valid and int_valid:
        print("ALL DATASETS VALIDATED SUCCESSFULLY.")
        print("=" * 65)
        return 0
    else:
        print("DATASET VALIDATION FAILED.")
        print("=" * 65)
        return 1


if __name__ == "__main__":
    sys.exit(run_validation())
