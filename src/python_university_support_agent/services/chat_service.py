# services/chat_service.py

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from langchain_core.documents import Document
from sqlalchemy.ext.asyncio import AsyncSession

from python_university_support_agent.crud import get_document_by_id
from python_university_support_agent.retrieval import get_vector_store, get_embeddings
from python_university_support_agent.schemas import ChatSourceItem, ChatMessageResponse
from python_university_support_agent.config import settings
from python_university_support_agent.logger import get_logger

import logging

logger = get_logger("Chat Service")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google_genai.models").setLevel(logging.ERROR)



embeddings = get_embeddings()
vector_store = get_vector_store(embeddings)


def verify_and_filter_resources(
    raw_results: List[Document],
    target_filename: Optional[str] = None
) -> List[Tuple[Document, str]]:
    """
    Carefully verifies and filters retrieved document chunks.
    Strips raw formatting artifacts and ensures resource relevance.
    Returns a list of tuples: (Document, cleaned_content_text).
    """
    logger.info("Executing Function: verify_and_filter_resources() | Candidate Chunks=%d | Target File=%s", len(raw_results), target_filename)
    verified_resources: List[Tuple[Document, str]] = []
    seen_contents = set()

    for doc in raw_results:
        source = doc.metadata.get("source", "")
        # Filter by document if doc_id was specified
        if target_filename:
            if source != target_filename and Path(source).name != target_filename:
                continue

        raw_text = doc.page_content or ""
        # Clean up whitespace and formatting artifacts
        cleaned_text = re.sub(r"\s+", " ", raw_text).strip()

        # Reject empty or minimal chunks
        if len(cleaned_text) < 15:
            continue

        # Prevent duplicate context snippets
        content_hash = cleaned_text[:100]
        if content_hash in seen_contents:
            continue

        seen_contents.add(content_hash)
        verified_resources.append((doc, cleaned_text))

    logger.info("Function: verify_and_filter_resources() Complete | Verified Chunks=%d", len(verified_resources))
    return verified_resources


def is_valid_api_key(key: Optional[str]) -> bool:
    """Checks if an API key is present and non-dummy."""
    if not key or not key.strip():
        return False
    k = key.strip().lower()
    if "your_" in k or "placeholder" in k or k in ("none", "null", "undefined"):
        return False
    return len(k) > 5


def synthesize_verified_reply(
    query: str,
    verified_resources: List[Tuple[Document, str]],
    model_id: Optional[str] = None
) -> str:
    """
    Synthesizes a response from verified resources without showing raw chunks or direct doc dumps.
    Uses Hugging Face models (or rule-based fallback).
    """
    logger.info("Executing Function: synthesize_verified_reply() | Verified Resources Count=%d | Model Config='%s'", len(verified_resources), model_id or settings.chat_model_id)

    if not verified_resources:
        logger.info("Function: synthesize_verified_reply() | No verified resources found.")
        return "No verified information matching your request was found in the document repository."

    target_model = model_id or settings.chat_model_id
    verified_facts = [cleaned for _, cleaned in verified_resources]
    context_str = "\n".join(f"- {fact}" for fact in verified_facts[:3])

    system_prompt = (
        "You are a helpful assistant. Explain the answer to the user in simple, clear, everyday language that is very easy for a human to read.\n"
        "Keep your response to 1 or 2 simple, direct sentences. Avoid complex jargon, stiff phrasing, or verbatim document chunk dumps."
    )
    user_prompt = f"Verified Facts:\n{context_str}\n\nUser Question: {query}"

    # Hugging Face Models Synthesis
    hf_token = os.getenv("HF_TOKEN") or settings.hf_token
    if is_valid_api_key(hf_token):
        hf_repo_id = target_model if "/" in target_model else "meta-llama/Llama-3.2-3B-Instruct"
        try:
            from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = HuggingFaceEndpoint(
                repo_id=hf_repo_id,
                huggingfacehub_api_token=hf_token.strip(),
                task="text-generation",
                max_new_tokens=100,
                temperature=0.1,
            )
            chat_model = ChatHuggingFace(llm=llm)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = chat_model.invoke(messages)
            reply_text = str(response.content).strip()
            if reply_text:
                logger.info("Reply Processed via Provider: Hugging Face API | Model: %s", hf_repo_id)
                return reply_text
            else:
                logger.warning("Hugging Face LLM returned empty response for model '%s'. Falling back to rule-based synthesizer.", hf_repo_id)
        except Exception as e:
            logger.warning("Hugging Face LLM synthesis failed for model '%s'. Error: %s. Falling back to rule-based synthesizer.", hf_repo_id, e)
    else:
        logger.info("HF_TOKEN is missing or not configured. Using rule-based simplified fact synthesizer.")




    # 4. Human-Readable Simplified Synthesizer (Fallback: 1-2 clean sentences)
    logger.info("Reply Processed via Fallback Engine: Human-Readable Simplified Fact Synthesizer")
    sentences: List[str] = []
    for _, text in verified_resources[:2]:
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent_clean = re.sub(r"^[^\w]+", "", sent.strip()) # Strip leading non-alphanumeric bullets/numbers
            if len(sent_clean) > 15 and sent_clean not in sentences:
                sentences.append(sent_clean)
            if len(sentences) >= 2:
                break
        if len(sentences) >= 2:
            break

    if not sentences:
        return "No verified concise answer could be found in the document."

    # Format into easy human-readable sentences
    final_reply = " ".join(sentences[:2])
    # Capitalize first character cleanly if needed
    if final_reply:
        final_reply = final_reply[0].upper() + final_reply[1:]

    return final_reply


async def process_chat_request(
    query: str,
    doc_id: Optional[int],
    k: int,
    db: AsyncSession,
    model_id: Optional[str] = None
) -> ChatMessageResponse:
    """
    Main chat processor:
    1. Verifies document target (if specified).
    2. Performs vector search.
    3. Carefully verifies resources.
    4. Synthesizes answer (no direct chunk dumps).
    5. Returns structured response with sources.
    """
    active_model = model_id or settings.chat_model_id
    search_scope = f"Document #{doc_id}" if doc_id is not None else "All Documents"
    logger.info("Service: process_chat_request() | query='%s' | Search Scope=%s | Model='%s'", query, search_scope, active_model)

    target_filename = None
    if doc_id is not None:
        doc = await get_document_by_id(db, doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found")
        target_filename = doc.filename

    # Retrieve candidate vector documents
    raw_results = vector_store.similarity_search(query=query, k=k)

    # Carefully verify and filter resources
    verified_items = verify_and_filter_resources(raw_results, target_filename=target_filename)

    # Synthesize clean reply without dumping raw chunks
    reply = synthesize_verified_reply(query, verified_items, model_id=model_id)

    # Build traceable sources list
    sources: List[ChatSourceItem] = []
    for doc_item, cleaned_text in verified_items:
        page_num = doc_item.metadata.get("page")
        source_name = doc_item.metadata.get("source", "Document")
        sources.append(
            ChatSourceItem(
                content=cleaned_text,
                source=str(source_name),
                page=int(page_num) if page_num is not None else None,
                metadata=doc_item.metadata
            )
        )

    logger.info("Service: process_chat_request() Completed Successfully | Sources Attached=%d", len(sources))
    return ChatMessageResponse(
        query=query,
        reply=reply,
        sources=sources
    )


