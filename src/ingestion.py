import base64
import json
import logging
from pathlib import Path
from typing import List

import ollama
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from src.config import DOCUMENTS_DIR, DATA_DIR, VISION_MODEL

logger = logging.getLogger(__name__)

def load_and_chunk_markdown() -> List[Document]:
    """Recursively load, split by headers, and then by character count."""
    md_files = list(DOCUMENTS_DIR.rglob("*.md"))
    logger.info(f"Found {len(md_files)} markdown files in {DOCUMENTS_DIR}")

    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
        ("####", "h4"),
    ]

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=100,
        add_start_index=True,
    )

    all_chunks = []
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            # Split by headers first
            header_splits = header_splitter.split_text(content)
            
            # Tracking chunks within this specific file
            file_chunk_index = 0
            
            # Further split long header-based chunks
            for i, split in enumerate(header_splits):
                # Attach file source metadata
                rel_path = md_file.relative_to(DOCUMENTS_DIR.parent).as_posix()
                
                # Compose section header for metadata
                h_vals = [split.metadata.get(h) for _, h in headers_to_split_on if h in split.metadata]
                section_header = " > ".join(h_vals) if h_vals else md_file.stem

                # Recursive character split
                sub_chunks = char_splitter.split_documents([split])
                for j, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.metadata.update({
                        "source": rel_path,
                        "section_header": section_header,
                        "chunk_index": file_chunk_index
                    })
                    all_chunks.append(sub_chunk)
                    file_chunk_index += 1
        except Exception as e:
            logger.error(f"Error processing {md_file}: {e}")

    logger.info(f"Created {len(all_chunks)} chunks from markdown files.")
    return all_chunks

def load_and_summarize_images(force: bool = False) -> List[Document]:
    """Find images, summarize using VISION_MODEL, and return as text chunks.
    Uses a local cache to skip images that haven't changed.
    """
    media_dir = DOCUMENTS_DIR / "media"
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    image_files = [f for f in media_dir.rglob("*") if f.suffix.lower() in image_extensions]
    
    logger.info(f"Found {len(image_files)} images in {media_dir}")

    # Load cache
    cache_path = DATA_DIR / "ingestion_cache.json"
    cache = {}
    if cache_path.exists() and not force:
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            logger.info(f"Loaded {len(cache)} cached image summaries.")
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")

    image_chunks = []
    cache_updated = False

    for img_path in image_files:
        try:
            rel_path = img_path.relative_to(DOCUMENTS_DIR.parent).as_posix()
            mtime = img_path.stat().st_mtime
            
            # Check cache
            if rel_path in cache and cache[rel_path].get("mtime") == mtime and not force:
                logger.info(f"Using cached summary for: {rel_path}")
                summary = cache[rel_path]["summary"]
            else:
                logger.info(f"Summarizing image: {rel_path}")
                with open(img_path, "rb") as img_file:
                    img_data = img_file.read()

                response = ollama.generate(
                    model=VISION_MODEL,
                    prompt="Describe this image in detail for a technical documentation search index. Focus on components, architecture diagrams, or UI elements shown.",
                    images=[base64.b64encode(img_data).decode()],
                    stream=False
                )
                summary = response.get("response", "")
                
                # Update cache
                cache[rel_path] = {"summary": summary, "mtime": mtime}
                cache_updated = True
            
            # Create a document for the summary
            doc = Document(
                page_content=summary,
                metadata={
                    "source": rel_path,
                    "type": "image_summary",
                    "section_header": img_path.stem,
                    "chunk_index": 0
                }
            )
            image_chunks.append(doc)
            
        except Exception as e:
            logger.error(f"Error summarizing {img_path}: {e}")

    # Save cache if needed
    if cache_updated:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
        logger.info(f"Updated cache at {cache_path}")

    logger.info(f"Generated {len(image_chunks)} image summary chunks.")
    return image_chunks
