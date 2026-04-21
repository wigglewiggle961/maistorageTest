from typing import TypedDict, Annotated, Sequence
import operator
import json
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from src.vectorstore import ChromaWrapper
from src import config

class AgentState(TypedDict):
    question: str
    generation: str
    documents: list[str]
    retries: int

def _get_llm(json_mode: bool = False, temperature: float = 0) -> ChatOllama:
    """Shared LLM factory to ensure consistent configuration."""
    kwargs = {
        "model": config.LLM_MODEL,
        "base_url": config.OLLAMA_BASE_URL,
        "temperature": temperature,
        "keep_alive": -1,
    }
    if json_mode:
        kwargs["format"] = "json"
    return ChatOllama(**kwargs)

def retrieve_node(state: AgentState):
    """Retrieve candidate documents from ChromaDB."""
    question = state["question"]
    vectorstore = ChromaWrapper()
    
    docs = vectorstore.similarity_search(query=question, k=config.RETRIEVAL_K)
    
    return {"documents": docs}

def transform_query_node(state: AgentState):
    """Expand and clarify the user's question before retrieval.
    
    NOTE: Currently inactive in the main graph. Use this to close the 
    vocabulary gap between conversational language and technical documentation.
    """
    question = state["question"]
    llm = _get_llm()

    system_prompt = (
        "You are a search query specialist for Azure AI Foundry Agent Service documentation.\n\n"
        "Your task is to rewrite the user's question into a high-precision technical search query "
        "that will maximize recall when run against a vector database of official Azure docs.\n\n"
        "Rules for rewriting:\n"
        "1. EXPAND product names - replace informal terms with their full official names:\n"
        "   - 'agents' → 'Azure AI Foundry Agent Service agents'\n"
        "   - 'MCP' → 'Model Context Protocol (MCP)'\n"
        "   - 'A2A' → 'Agent-to-Agent (A2A) tool'\n"
        "2. RESOLVE abbreviations and acronyms fully (RBAC → role-based access control).\n"
        "3. DECOMPOSE multi-part questions - if the question asks about more than one topic "
        "(e.g., cold starts AND regional availability), separate them with semicolons so each "
        "sub-question can match a different chunk.\n"
        "4. ADD technical context - if the user asks about an error or a 'why', include the "
        "likely technical concept (e.g., 'Unauthorized' → 'tool authentication RBAC role assignment agent identity').\n"
        "5. PRESERVE intent - do not change what the user is asking for, only how it is expressed.\n"
        "6. OUTPUT ONLY the transformed query — no preamble, no explanation, no quotation marks."
    )

    response = llm.invoke([
        ("system", system_prompt),
        ("human", f"Original question: {question}\n\nTransformed query:")
    ])

    transformed = response.content.strip()
    # Strip common model preamble patterns
    for prefix in ["Here's", "Here is", "Transformed:", "Query:", "Rewritten:"]:
        if transformed.lower().startswith(prefix.lower()):
            transformed = transformed[len(prefix):].lstrip(":").strip()

    print(f"--- TRANSFORM: '{question[:60]}...' → '{transformed[:80]}...' ---")
    return {"question": transformed}



def window_node(state: AgentState):
    """Expand retrieved chunks with their immediate context neighbors."""
    documents = state["documents"]
    vectorstore = ChromaWrapper()
    
    all_expanded_docs = []
    seen_ids = set()
    
    for i, doc in enumerate(documents):
        # Selective windowing: only expand the top-N results to reduce latency/noise
        if i < config.WINDOW_TOP_K:
            source = doc.metadata.get("source")
            index = doc.metadata.get("chunk_index")
            
            if source is None or index is None:
                if doc.id not in seen_ids:
                    all_expanded_docs.append(doc)
                    seen_ids.add(doc.id)
                continue
                
            # Define range for fetching neighbors
            start_idx = max(0, index - config.WINDOW_SIZE)
            end_idx = index + config.WINDOW_SIZE
            
            # Fetch original chunk + neighbors from the same source
            neighbors = vectorstore.vectorstore.get(
                where={
                    "$and": [
                        {"source": {"$eq": source}},
                        {"chunk_index": {"$gte": start_idx}},
                        {"chunk_index": {"$lte": end_idx}}
                    ]
                }
            )
            
            # Reconstruct Document objects from results
            window_docs = []
            for j in range(len(neighbors["documents"])):
                content = neighbors["documents"][j]
                meta = neighbors["metadatas"][j]
                doc_id = neighbors["ids"][j]
                window_docs.append(Document(page_content=content, metadata=meta, id=doc_id))
                
            # Sort THIS window by chunk_index to ensure logical flow
            window_docs.sort(key=lambda d: d.metadata.get("chunk_index", 0))
            
            # MERGE Optimization: Join the whole window into a single document block
            # This keeps the 'Golden Hit' and its context together as Rank 0
            merged_content = "\n\n".join([d.page_content for d in window_docs])
            merged_doc = Document(page_content=merged_content, metadata=doc.metadata, id=f"merged_{doc.id}")
            
            if merged_doc.id not in seen_ids:
                all_expanded_docs.append(merged_doc)
                seen_ids.add(merged_doc.id)
        else:
            # For documents beyond WINDOW_TOP_K, include them without neighbor expansion
            if doc.id not in seen_ids:
                all_expanded_docs.append(doc)
                seen_ids.add(doc.id)
                
    # Format documents as strings with metadata for citation in prompt
    formatted = []
    for doc in all_expanded_docs:
        source = doc.metadata.get("source", "unknown")
        section = doc.metadata.get("section_header", "unknown")
        content = doc.page_content
        formatted.append(f"SOURCE: {source}\nSECTION: {section}\nCONTENT: {content}")
        
    return {"documents": formatted}

class RouteQuery(BaseModel):
    """Boolean result for query routing."""
    is_relevant: bool = Field(description="Whether the query is about Azure AI Foundry Agents")

def route_query(state: AgentState) -> str:
    """Route the query to retrieval or out of scope."""
    question = state["question"]
    
    llm = _get_llm(json_mode=True)
    
    system_prompt = (
        "You are a query classifier for an Azure AI Foundry Agent Service documentation assistant.\n\n"
        "Your goal is to decide if the question CAN be answered using Azure AI Foundry Agent Service docs.\n\n"
        "IMPORTANT: Users often ask questions using domain-implicit language without naming the product explicitly.\n"
        "Questions about 'agents', 'basic setup', 'standard setup', 'threads', 'runs', 'tools', "
        "'connections', 'capability hosts', 'tracing', 'evaluation', or 'agent setup' are IN-SCOPE.\n\n"
        "Return is_relevant=true if the question could plausibly be answered by Azure AI Foundry Agent Service docs.\n"
        "Return is_relevant=false ONLY if the question is clearly about something unrelated, such as:\n"
        "- General cooking, sports, history, or non-technical topics\n"
        "- Other Microsoft products with no connection to AI agents (e.g., 'How do I use Excel?')\n"
        "- Broad 'What is AI?' style questions with no product specificity\n\n"
        "When in doubt, return is_relevant=true and let the retriever decide.\n\n"
        "Respond with ONLY this JSON format, no other text:\n"
        "{\"is_relevant\": true}\n"
        "or\n"
        "{\"is_relevant\": false}"
    )
    
    response = llm.invoke([
        ("system", system_prompt),
        ("human", f"Classify this question:\n{question}")
    ])
    
    try:
        result = json.loads(response.content)
        if not result.get("is_relevant", True):  # Default to retrieve on parse failure or ambiguity
            return "out_of_scope"
        return "retrieve"
    except Exception:
        # If parsing fails, default to retrieve — better to attempt retrieval than silently reject
        return "retrieve"

class GradeResult(BaseModel):
    """Boolean result for document relevance grading."""
    is_relevant: bool = Field(description="Whether the document is relevant to the question")

def grade_node(state: AgentState):
    """Filter retrieved documents based on relevance in a single batch call.
    
    OPTIMIZATION: Documents are graded in batches rather than individually to 
    minimize latency and context-switching overhead.
    """
    question = state["question"]
    documents = state["documents"]
    
    if not documents:
        return {"documents": []}

    llm = _get_llm(json_mode=True)
    
    # Format all documents into a single block with clear indices
    docs_formatted = "\n\n".join([f"DOC {i}:\n{doc}" for i, doc in enumerate(documents)])
    
    system_prompt = (
        "You are a relevance judge evaluating whether documents should be retrieved to answer a user's question.\n\n"
        "Your task: for each document, decide if it meaningfully helps answer the question — not just mentions related words.\n\n"
        "Mark a document TRUE only if it:\n"
        "- Directly answers the question, or\n"
        "- Contains specific facts, data, or explanations that are necessary to construct a good answer\n\n"
        "Mark a document FALSE if it:\n"
        "- Only mentions the topic in passing or as background noise\n"
        "- Is about a related subject but doesn't address what the question is actually asking\n"
        "- Would not change or improve the answer if it were removed\n\n"
        "Think step by step: re-read the question, identify exactly what it is asking for, "
        "then judge each document against that specific need and if the document is actually useful.\n\n"
        "Respond with ONLY this JSON format:\n"
        "{\"relevance_results\": [true, false, true]}"
    )
    
    human_prompt = f"Question: {question}\n\nDocuments:\n{docs_formatted}"
    
    response = llm.invoke([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    try:
        result = json.loads(response.content)
        relevance_list = result.get("relevance_results", [])
        
        # Guard: if model returned wrong count, fall back to keeping all
        if len(relevance_list) != len(documents):
            print(f"--- GRADER: Model returned {len(relevance_list)} results for {len(documents)} docs. Keeping all. ---")
            return {"documents": documents}

        filtered_docs = []
        for i, is_relevant in enumerate(relevance_list):
            if is_relevant:
                filtered_docs.append(documents[i])
        
        print(f"--- GRADER: {len(filtered_docs)}/{len(documents)} documents kept ---")
        return {"documents": filtered_docs}
    except Exception:
        # Fallback to keep all documents if batch grading fails
        print("--- GRADER: Failed to parse relevance results. Keeping all. ---")
        return {"documents": documents}

def generate_node(state: AgentState):
    """Generate an answer grounded only in the retrieved context."""
    question = state["question"]
    documents = state["documents"]
    
    llm = _get_llm()
    
    if not documents:
        return {"generation": "I could not find relevant documentation in the knowledge base."}
    
    # Format context and track sources for citations
    # Apply hard cap to prevent context dilution/overflow
    documents = documents[:config.MAX_CONTEXT_CHUNKS]
    context_str = "\n\n".join(documents)
    
    # The plan requires inline citations [1] and a footnote map.
    # The context is provided as a list of strings.
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
    
    return {"generation": response.content, "documents": documents}

class HallucinationCheck(BaseModel):
    """Boolean result for hallucination check."""
    is_grounded: bool = Field(description="Whether the answer is fully grounded by context")

def check_hallucination(state: AgentState) -> str:
    """Check if the generated answer is grounded in the retrieved documents."""
    generation = state["generation"]
    documents = state["documents"]
    retries = state.get("retries", 0)
    
    # Cap total retries to prevent infinite loops (hallucination -> rewrite loop)
    if retries >= config.MAX_RETRIES:
        return "useful"

    # If we already returned the 'not found' message, it's 'useful' (terminal)
    if "I could not find relevant documentation" in generation:
        return "useful"

    llm = _get_llm(json_mode=True)
    
    context_str = "\n\n".join(documents)
    
    system_prompt = (
        "You are a grounding verifier. Check if the answer is supported by the provided context.\n\n"
        "Rules:\n"
        "- is_grounded=true: ALL factual claims in the answer appear in the context\n"
        "- is_grounded=false: The answer contains claims NOT found in the context\n"
        "- Paraphrasing is acceptable — the meaning must match, not exact wording\n"
        "- If the answer says it could not find information, that is grounded (true)\n\n"
        "Respond with ONLY this JSON:\n"
        "{\"is_grounded\": true}\n"
        "or\n"
        "{\"is_grounded\": false}"
    )

    response = llm.invoke([
        ("system", system_prompt),
        ("human", f"CONTEXT:\n{context_str}\n\nANSWER TO CHECK:\n{generation}")
    ])
    
    try:
        result = json.loads(response.content)
        if result.get("is_grounded", False):
            # Check if it actually addresses the question (utility check omitted for simplicity)
            return "useful"
    except Exception:
        pass
        
    return "not_supported"

def rewrite_node(state: AgentState):
    """Reformulate the question for re-retrieval."""
    question = state["question"]
    retries = state.get("retries", 0)
    
    llm = _get_llm()
    
    system_prompt = (
        "You are a search query optimizer for Azure AI Foundry Agent Service documentation.\n\n"
        "Rewrite the user's question to improve vector similarity search results.\n"
        "Guidelines:\n"
        "- Use specific Azure AI Foundry terminology\n"
        "- Expand abbreviations (e.g., 'agents' → 'Azure AI Foundry Agent Service agents')\n"
        "- Keep the core intent identical\n"
        "- Output ONLY the rewritten question — no explanations, no prefixes"
    )

    response = llm.invoke([
        ("system", system_prompt),
        ("human", f"Original question: {question}\n\nRewritten question:")
    ])

    rewritten = response.content.strip()
    # Remove common prefixes the model might add
    for prefix in ["Here's", "Here is", "Rewritten:", "Reformulated:"]:
        if rewritten.lower().startswith(prefix.lower()):
            rewritten = rewritten[len(prefix):].lstrip(":").strip()
    
    return {"question": rewritten, "retries": retries + 1}

def decide_to_generate(state: AgentState):
    """Determine whether to generate an answer, rewrite the query, or check for hallucinations."""
    documents = state["documents"]
    retries = state.get("retries", 0)
    
    if not documents:
        if retries < config.MAX_RETRIES:
            return "rewrite"
        else:
            return "generate"
    else:
        # We have docs, proceed to generation node
        return "generate"

def compile_graph():
    """Assemble the LangGraph state machine."""
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade", grade_node)
    workflow.add_node("window", window_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("rewrite", rewrite_node)
    
    # Special node for out of scope
    def out_of_scope_node(state):
        return {"generation": "I can only answer questions about Azure AI Foundry Agent Service."}
    workflow.add_node("out_of_scope", out_of_scope_node)
    
    # Set Conditional Entry Point
    workflow.set_conditional_entry_point(
        route_query,
        {"retrieve": "retrieve", "out_of_scope": "out_of_scope"}
    )
    
    # Define Edges
    workflow.add_edge("retrieve", "window")
    workflow.add_edge("window", "grade")
    
    workflow.add_conditional_edges(
        "grade",
        decide_to_generate,
        {
            "rewrite": "rewrite",
            "generate": "generate"
        }
    )
    
    workflow.add_conditional_edges(
        "generate",
        check_hallucination,
        {
            "useful": END,
            "not_supported": "rewrite"
        }
    )
    
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("out_of_scope", END)
    
    return workflow.compile()

def run_agent(question: str) -> dict:
    """Public entry point for programmatic use by the evaluation harness.
    
    Returns:
        dict with keys:
            "answer": str - the final generated answer
            "contexts": list[str] - the formatted document strings used for generation
    """
    graph = compile_graph()
    result = graph.invoke({"question": question, "generation": "", "documents": [], "retries": 0})
    return {
        "answer": result.get("generation", ""),
        "contexts": result.get("documents", [])
    }
