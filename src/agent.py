from typing import TypedDict, Annotated, Sequence
import operator
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

def retrieve_node(state: AgentState):
    """Retrieve documents from ChromaDB based on the question."""
    question = state["question"]
    vectorstore = ChromaWrapper()
    
    # Retrieve top-k chunks. Using k=4 as per plan.
    docs = vectorstore.similarity_search(query=question, k=4)
    
    # Format docs as strings with metadata for citation
    formatted_docs = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        section = doc.metadata.get("section_header", "unknown")
        content = doc.page_content
        formatted_docs.append(f"SOURCE: {source}\nSECTION: {section}\nCONTENT: {content}")
    
    return {"documents": formatted_docs}

class RouteQuery(BaseModel):
    """Boolean result for query routing."""
    is_relevant: bool = Field(description="Whether the query is about Azure AI Foundry Agents")

def route_query(state: AgentState) -> str:
    """Route the query to retrieval or out of scope."""
    question = state["question"]
    
    llm = ChatOllama(
        model=config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0,
        format="json",
        keep_alive=-1
    )
    
    system_prompt = (
        "You are an expert router. Route the user question to either 'Azure AI Foundry Agents' (True) "
        "or 'Out of Scope' (False). Ignore general Azure or general IT questions."
    )
    
    response = llm.invoke([
        ("system", system_prompt),
        ("human", f"Question: {question}\nReturn JSON with 'is_relevant': bool")
    ])
    
    try:
        import json
        result = json.loads(response.content)
        if result.get("is_relevant", False):
            return "retrieve"
    except Exception:
        pass
        
    return "out_of_scope"

class GradeResult(BaseModel):
    """Boolean result for document relevance grading."""
    is_relevant: bool = Field(description="Whether the document is relevant to the question")

def grade_node(state: AgentState):
    """Filter retrieved documents based on relevance in a single batch call."""
    question = state["question"]
    documents = state["documents"]
    
    if not documents:
        return {"documents": []}

    llm = ChatOllama(
        model=config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0,
        format="json",
        keep_alive=-1
    )
    
    # Format all documents into a single block with clear indices
    docs_formatted = "\n\n".join([f"DOC {i}:\n{doc}" for i, doc in enumerate(documents)])
    
    system_prompt = (
        "Assess whether each of the following document chunks is relevant to the user question. "
        "Return a JSON object with a key 'relevance_results' containing a list of booleans "
        "matching the order of the documents provided."
    )
    
    human_prompt = f"Question: {question}\n\nDocuments:\n{docs_formatted}"
    
    response = llm.invoke([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    try:
        import json
        result = json.loads(response.content)
        relevance_list = result.get("relevance_results", [])
        
        filtered_docs = []
        for i, is_relevant in enumerate(relevance_list):
            if is_relevant and i < len(documents):
                filtered_docs.append(documents[i])
        
        return {"documents": filtered_docs}
    except Exception:
        # Fallback to keep all documents if batch grading fails
        return {"documents": documents}

def generate_node(state: AgentState):
    """Generate an answer grounded only in the retrieved context."""
    question = state["question"]
    documents = state["documents"]
    
    llm = ChatOllama(
        model=config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0,
        keep_alive=-1
    )
    
    if not documents:
        return {"generation": "I could not find relevant documentation in the knowledge base."}
    
    # Format context and track sources for citations
    context_str = "\n\n".join(documents)
    
    # The plan requires inline citations [1] and a footnote map.
    # The context is provided as a list of strings.
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
    
    return {"generation": response.content}

class HallucinationCheck(BaseModel):
    """Boolean result for hallucination check."""
    is_grounded: bool = Field(description="Whether the answer is fully grounded by context")

def check_hallucination(state: AgentState) -> str:
    """Check if the generated answer is grounded in the retrieved documents."""
    generation = state["generation"]
    documents = state["documents"]
    
    # If we already returned the 'not found' message, it's 'useful' (terminal)
    if "I could not find relevant documentation" in generation:
        return "useful"

    llm = ChatOllama(
        model=config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0,
        format="json",
        keep_alive=-1
    )
    
    context_str = "\n\n".join(documents)
    
    response = llm.invoke([
        ("system", "Determine if the following answer is fully grounded by and supported by the context. Return JSON with 'is_grounded': bool."),
        ("human", f"Context: {context_str}\n\nAnswer: {generation}")
    ])
    
    try:
        import json
        result = json.loads(response.content)
        if result.get("is_grounded", False):
            # Check if it actually addresses the question (utility check omitted for simplicity but implied)
            return "useful"
    except Exception:
        pass
        
    return "not_supported"

def rewrite_node(state: AgentState):
    """Reformulate the question for re-retrieval."""
    question = state["question"]
    retries = state.get("retries", 0)
    
    llm = ChatOllama(
        model=config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0,
        keep_alive=-1
    )
    
    response = llm.invoke(f"Reformulate the following question to improve dense retrieval from a vector store based on Azure AI Foundry Agent documentation. Original question: {question}")
    
    return {"question": response.content, "retries": retries + 1}

def decide_to_generate(state: AgentState):
    """Determine whether to generate an answer, rewrite the query, or check for hallucinations."""
    documents = state["documents"]
    retries = state.get("retries", 0)
    
    if not documents:
        if retries < 3:
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
    workflow.add_edge("retrieve", "grade")
    
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
