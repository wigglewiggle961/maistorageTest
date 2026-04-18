import json
import sys
import re
from pathlib import Path

# Provide access to the project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import EVAL_DATASET_PATH

def extract_key_terms(text: str) -> set[str]:
    """Extract content words (length > 4) from text, lowercased."""
    words = re.findall(r"\b[a-z]{5,}\b", text.lower())
    # Remove stop words
    stopwords = {"which", "their", "there", "these", "would", "could", "should",
                 "about", "after", "before", "learn", "using", "where", "other",
                 "azure", "foundry", "agent", "agents", "service"}
    return {w for w in words if w not in stopwords}

def validate_item(item: dict) -> dict:
    """Return a validation report dict for a single dataset item."""
    question = item.get("question", "")
    ground_truth = item.get("ground_truth", "")
    source_chunks = item.get("source_chunks", [])
    verified = item.get("verified", False)

    gt_terms = extract_key_terms(ground_truth)
    if not gt_terms:
        return {"question": question, "status": "SKIP", "reason": "No key terms in ground_truth"}

    # Aggregate all chunk text
    all_chunk_text = " ".join(source_chunks).lower()
    chunk_terms = extract_key_terms(all_chunk_text)

    overlap = gt_terms & chunk_terms
    overlap_ratio = len(overlap) / len(gt_terms) if gt_terms else 0

    if overlap_ratio < 0.30:
        status = "FLAG"
        reason = (
            f"Only {overlap_ratio:.0%} of ground_truth key terms found in source_chunks. "
            f"Missing: {sorted(gt_terms - chunk_terms)[:5]}"
        )
    elif not verified:
        status = "UNVERIFIED"
        reason = "Marked verified=false in dataset — may need human review."
    else:
        status = "OK"
        reason = f"{overlap_ratio:.0%} key term coverage in source_chunks."

    return {
        "question": question,
        "status": status,
        "reason": reason,
        "overlap_ratio": round(overlap_ratio, 3),
        "verified": verified,
    }

def main():
    if not EVAL_DATASET_PATH.exists():
        print(f"ERROR: Dataset not found at {EVAL_DATASET_PATH}")
        sys.exit(1)

    with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"Validating {len(dataset)} items in {EVAL_DATASET_PATH}...\n")

    results = [validate_item(item) for item in dataset]

    ok = [r for r in results if r["status"] == "OK"]
    flagged = [r for r in results if r["status"] == "FLAG"]
    unverified = [r for r in results if r["status"] == "UNVERIFIED"]

    print(f"✓ Passed:     {len(ok)}")
    print(f"⚠ Unverified: {len(unverified)}")
    print(f"✗ Flagged:    {len(flagged)}\n")

    if flagged:
        print("=== FLAGGED ITEMS (low source chunk coverage) ===")
        for r in flagged:
            print(f"\n  Q: {r['question'][:80]}")
            print(f"     Reason: {r['reason']}")

    if unverified:
        print("\n=== UNVERIFIED ITEMS (human review needed) ===")
        for r in unverified:
            print(f"\n  Q: {r['question'][:80]}")

    # Exit non-zero if there are flagged items, for potential CI use
    sys.exit(1 if flagged else 0)

if __name__ == "__main__":
    main()
