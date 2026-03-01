"""
Prompt templates for the PIM AI Coach.

Domain-specific system prompts and question-answering templates that ground
the LLM in PIM best practices and retrieved policy documents.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_PROMPT = """\
You are the PIM AI Coach — an expert assistant on Public Investment Management (PIM).
Your role is to help government officials, policy makers, and development practitioners
understand and improve public investment processes.

You draw on a database of international PIM policy documents including:
- Primary legislation and legal frameworks
- Secondary regulations and decrees
- Procedural guidelines and methodological guidance
- National and sectoral investment strategies

When answering questions:
1. Ground your answers in the retrieved policy documents provided as context.
2. Cite specific documents by country and title when referencing policies.
3. Compare approaches across countries when relevant.
4. Distinguish between different tiers of policy guidance (legislation vs. guidelines vs. strategies).
5. If the context does not contain enough information, say so clearly and suggest
   what additional documents or topics the user might explore.
6. Use clear, professional language appropriate for a government policy audience.

{context_instruction}"""

CONTEXT_INSTRUCTION_WITH_DOCS = """\
Below are relevant excerpts from PIM policy documents. Use them to answer the question.

--- Retrieved Documents ---
{context}
--- End of Documents ---"""

CONTEXT_INSTRUCTION_NO_DOCS = """\
No specific policy documents were retrieved for this question.
Answer based on your general knowledge of PIM best practices, and note that
the answer is not grounded in specific policy documents from the database."""


def get_rag_prompt() -> ChatPromptTemplate:
    """Prompt template for RAG Q&A with retrieved context."""
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{question}"),
    ])


def get_condense_prompt() -> ChatPromptTemplate:
    """Prompt to condense chat history + follow-up into a standalone question."""
    return ChatPromptTemplate.from_messages([
        ("system",
         "Given the chat history and a follow-up question, rephrase the "
         "follow-up as a standalone question that captures the full context. "
         "Do not answer the question — just rephrase it."),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ])


def format_documents(docs) -> str:
    """Format retrieved documents into a context string for the prompt."""
    if not docs:
        return ""

    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        header_parts = []
        if meta.get("country_name") or meta.get("country"):
            header_parts.append(meta.get("country_name") or meta.get("country"))
        if meta.get("name_eng"):
            header_parts.append(meta["name_eng"])
        if meta.get("year"):
            header_parts.append(str(meta["year"]))

        header = " — ".join(header_parts) if header_parts else f"Document {i}"
        tier = meta.get("policy_guidance_tier")
        tier_label = {1: "Legislation", 2: "Regulation", 3: "Guidelines", 4: "Strategy"}.get(tier, "")

        parts.append(
            f"[{i}] {header}"
            + (f" ({tier_label})" if tier_label else "")
            + f"\n{doc.page_content}"
        )

    return "\n\n".join(parts)
