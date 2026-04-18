import json
import logging
import re
from pathlib import Path
from typing import List, Set

import yaml
from src.config import DOCUMENTS_DIR, EVAL_DATASET_PATH
from src.vectorstore import ChromaWrapper

logger = logging.getLogger(__name__)

def _get_keywords(text: str) -> Set[str]:
    """Extract a set of lowercased alphanumeric keywords from text."""
    # Simple regex to find words, filtering out short/common stop words could be better 
    # but for a simple heuristic, set intersection of words works.
    words = re.findall(r'\b\w{3,}\b', text.lower())
    # Exclude basic common words (manual stop list for better precision)
    stop_words = {"the", "and", "your", "that", "this", "with", "from", "for", "are", "can"}
    return {w for w in words if w not in stop_words}

def build_eval_dataset(vectorstore: ChromaWrapper):
    """Parse FAQ YAMLs, retrieve context, verify, and save as JSON."""
    faq_paths = [
        DOCUMENTS_DIR / "faq.yml",
        DOCUMENTS_DIR / "concepts" / "foundry-iq-faq.yml"
    ]
    
    eval_data = []
    
    for faq_path in faq_paths:
        if not faq_path.exists():
            logger.warning(f"FAQ file not found: {faq_path}")
            continue
            
        logger.info(f"Parsing FAQ: {faq_path}")
        with open(faq_path, "r", encoding="utf-8") as f:
            # Handle YamlMime header if present
            content = f.read()
            if content.startswith("### YamlMime:FAQ"):
                content = "\n".join(content.split("\n")[1:])
            
            data = yaml.safe_load(content)
            
        for section in data.get("sections", []):
            for item in section.get("questions", []):
                question = item.get("question", "").strip()
                answer = item.get("answer", "").strip()
                
                if not question or not answer:
                    continue
                
                # Retrieve top chunks for this question
                retrieved_docs = vectorstore.similarity_search(question, k=5)
                retrieved_texts = [doc.page_content for doc in retrieved_docs]
                
                # Heuristic Verification
                answer_keywords = _get_keywords(answer)
                combined_retrieved = " ".join(retrieved_texts)
                retrieved_keywords = _get_keywords(combined_retrieved)
                
                intersection = answer_keywords.intersection(retrieved_keywords)
                
                # If at least 30% of answer keywords are in retrieved text, mark as verified
                verified = False
                if answer_keywords:
                    overlap_ratio = len(intersection) / len(answer_keywords)
                    if overlap_ratio >= 0.3:
                        verified = True
                
                eval_data.append({
                    "question": question,
                    "ground_truth": answer,
                    "source_chunks": retrieved_texts,
                    "verified": verified
                })

    # Ensure data directory exists
    EVAL_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(EVAL_DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2)
        
    logger.info(f"Built evaluation dataset with {len(eval_data)} pairs at {EVAL_DATASET_PATH}")
