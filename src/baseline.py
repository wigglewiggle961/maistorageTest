from langchain_ollama import ChatOllama
from src.vectorstore import ChromaWrapper
from src import config

def run_baseline(question: str) -> dict:
    """Run a single-shot RAG baseline (Retrieve -> Generate).
    
    No agentic loops, grading, or hallucination checks.
    Uses the same prompt and LLM as the agent for fair comparison.
    """
    # 1. Retrieve
    vectorstore = ChromaWrapper()
    docs = vectorstore.similarity_search(query=question, k=config.MAX_CONTEXT_CHUNKS)
    
    # 2. Format Context
    formatted_docs = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        section = doc.metadata.get("section_header", "unknown")
        content = doc.page_content
        formatted_docs.append(f"SOURCE: {source}\nSECTION: {section}\nCONTENT: {content}")
    
    context_str = "\n\n".join(formatted_docs)
    
    # 3. Generate
    llm = ChatOllama(
        model=config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0,
        keep_alive=-1
    )
    
    system_prompt = (
        "You are a technical assistant for Azure AI Foundry Agent Service documentation.\n\n"
        "STRICT RULES:\n"
        "1. Answer ONLY using the provided context blocks. Do NOT use outside knowledge.\n"
        "2. If the context does not contain the answer, respond with exactly: "
        "\"I could not find relevant documentation in the knowledge base.\"\n"
        "3. Cite sources using [1], [2], etc. where [1] is the first context block, [2] is the second, and so on.\n"
        "4. Every factual claim must have a citation.\n"
        "5. Do NOT add a Sources or References section — the UI adds citations automatically.\n\n"
        "Context blocks follow, numbered in order."
    )
    
    response = llm.invoke([
        ("system", system_prompt),
        ("human", f"Context:\n{context_str}\n\nQuestion: {question}")
    ])
    
    return {
        "answer": response.content,
        "contexts": formatted_docs
    }
