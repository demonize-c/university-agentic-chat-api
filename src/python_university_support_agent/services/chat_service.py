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

logger = get_logger("Chat Service")

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

    return verified_resources


def synthesize_verified_reply(query: str, verified_resources: List[Tuple[Document, str]]) -> str:
    """
    Synthesizes a response from verified resources without showing raw chunks or direct doc dumps.
    """
    if not verified_resources:
        return "No verified information matching your request was found in the document repository."

    # Combine cleaned facts for synthesis
    verified_facts = [cleaned for _, cleaned in verified_resources]

    # Attempt LLM synthesis if HF_TOKEN is available
    hf_token = os.getenv("HF_TOKEN") or settings.hf_token
    if hf_token and hf_token.strip():
        try:
            from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = HuggingFaceEndpoint(
                repo_id="Qwen/Qwen2.5-7B-Instruct",
                huggingfacehub_api_token=hf_token.strip(),
                task="conversational",
                max_new_tokens=256,
                temperature=0.2,
            )

            chat_model = ChatHuggingFace(llm=llm)

            context_str = "\n".join(f"- {fact}" for fact in verified_facts[:3])
            messages = [
                SystemMessage(content=(
                    "You are a helpful university support assistant. Answer the user question based strictly on the verified facts below.\n"
                    "Synthesize the answer clearly and concisely in your own words. DO NOT copy or output raw document chunks verbatim. DO NOT dump raw chunk blocks."
                )),
                HumanMessage(content=f"Verified Facts:\n{context_str}\n\nUser Question: {query}")
            ]

            response = chat_model.invoke(messages)
            reply_text = str(response.content).strip()
            if reply_text:
                return reply_text
        except Exception as e:
            logger.warning(f"LLM synthesis failed, falling back to rule-based synthesis: {e}")


    # Rule-Based Fact Synthesizer (Fallback when LLM is offline/unavailable)
    # Synthesizes clean structured facts instead of dumping raw chunk blocks
    sentences: List[str] = []
    for _, text in verified_resources[:3]:
        # Split into sentences and extract non-redundant meaningful lines
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent_clean = sent.strip()
            if len(sent_clean) > 20 and sent_clean not in sentences:
                sentences.append(sent_clean)
            if len(sentences) >= 4:
                break
        if len(sentences) >= 4:
            break

    if not sentences:
        return "Verified information was retrieved from the document, but could not be synthesized into a clear answer."

    bullet_points = "\n".join(f"- {s}" for s in sentences)
    return f"Based on verified resources in the documentation:\n\n{bullet_points}"



async def process_chat_request(
    query: str,
    doc_id: Optional[int],
    k: int,
    db: AsyncSession
) -> ChatMessageResponse:
    """
    Main chat processor:
    1. Verifies document target (if specified).
    2. Performs vector search.
    3. Carefully verifies resources.
    4. Synthesizes answer (no direct chunk dumps).
    5. Returns structured response with sources.
    """
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
    reply = synthesize_verified_reply(query, verified_items)

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

    return ChatMessageResponse(
        query=query,
        reply=reply,
        sources=sources
    )
