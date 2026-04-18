import sys
import argparse
import logging
from pathlib import Path

# Add project root to sys.path to allow imports from src
sys.path.append(str(Path(__file__).parent.parent))

from src.ingestion import load_and_chunk_markdown, load_and_summarize_images
from src.vectorstore import ChromaWrapper
from src.faq_parser import build_eval_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ingest_cli")

def main():
    parser = argparse.ArgumentParser(description="Ingest markdown and images into ChromaDB.")
    parser.add_argument("--force", action="store_true", help="Force re-summarization of images.")
    args = parser.parse_args()

    logger.info("Starting Agentic RAG Ingestion Pipeline...")

    try:
        # 1. Initialize VectorStore
        vectorstore = ChromaWrapper()
        
        # 2. Process Markdown
        logger.info("--- Step 1: Processing Markdown ---")
        md_docs = load_and_chunk_markdown()
        
        # 3. Process Images
        logger.info("--- Step 2: Processing Images ---")
        img_docs = load_and_summarize_images(force=args.force)
        
        # 4. Upsert to ChromaDB
        logger.info("--- Step 3: Storing in ChromaDB ---")
        all_docs = md_docs + img_docs
        vectorstore.add_documents(all_docs)
        
        # 5. Build Evaluation Dataset
        logger.info("--- Step 4: Building Evaluation Dataset ---")
        build_eval_dataset(vectorstore)
        
        # 6. Report Stats
        stats = vectorstore.collection_stats()
        logger.info("--- Ingestion Complete ---")
        logger.info(f"Total Markdown Chunks: {len(md_docs)}")
        logger.info(f"Total Image Summaries: {len(img_docs)}")
        logger.info(f"Final Collection Size: {stats['total_chunks']} chunks")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
