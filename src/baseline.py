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
    docs = vectorstore.similarity_search(query=question, k=config.TOP_K)
    
    # 2. Format Context (MUST match src/agent.py formatting)
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
        "You are a technical assistant answering questions about Azure AI Foundry Agents. "
        "Use ONLY the provided context blocks to answer the question. "
        "If the answer is not in the context, say you don't know.\n\n"
        "Style Requirement: Use inline citations like [1], [2] to reference the context blocks. "
        "The context blocks are provided in order: the first block is [1], the second is [2], etc. "
        "YOU MUST cite every block that you use for information. "
        "DO NOT include a 'Sources' or 'References' section at the end of your response, "
        "as the UI will handle this automatically."
    )
    
    response = llm.invoke([
        ("system", system_prompt),
        ("human", f"Context:\n{context_str}\n\nQuestion: {question}")
    ])
    
    return {
        "answer": response.content,
        "contexts": formatted_docs
    }
