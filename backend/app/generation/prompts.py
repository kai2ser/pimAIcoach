"""
Prompt templates for the PIM AI Coach.

Domain-specific system prompts and question-answering templates that ground
the LLM in PIM best practices and retrieved policy documents.
"""

from __future__ import annotations

from functools import lru_cache

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
{language_instruction}
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

# -- Language instructions ------------------------------------------------- #

LANGUAGE_INSTRUCTION_DEFAULT = ""

LANGUAGE_INSTRUCTION_ORIGINAL = """
IMPORTANT: The user is working with original-language policy documents.
- The retrieved documents are in their original language (not English).
- The user's question is in the original language.
- You MUST respond in the same language as the retrieved documents.
- Cite document titles using their original names (name_orig) when available.
- If documents are in multiple languages, respond in the language that matches
  the majority of retrieved documents."""


@lru_cache(maxsize=1)
def get_rag_prompt() -> ChatPromptTemplate:
    """Prompt template for RAG Q&A with retrieved context."""
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{question}"),
    ])


@lru_cache(maxsize=1)
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


@lru_cache(maxsize=1)
def _get_tokenizer():
    """Return a cached tiktoken encoder for accurate token counting."""
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def _estimate_tokens(text: str) -> int:
    """Count tokens using tiktoken when available, else fall back to heuristic."""
    enc = _get_tokenizer()
    if enc is not None:
        return len(enc.encode(text, disallowed_special=()))
    return len(text) // 4


# Leave headroom for system prompt + answer generation
_MAX_CONTEXT_TOKENS = 6000


def format_documents(docs, max_context_tokens: int = _MAX_CONTEXT_TOKENS) -> str:
    """Format retrieved documents into a context string for the prompt.

    Automatically truncates to stay within *max_context_tokens* so the
    combined prompt never exceeds the model's context window.
    """
    if not docs:
        return ""

    parts: list[str] = []
    running_tokens = 0

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

        lang_info = ""
        if meta.get("lang_type"):
            lang_info = f" [{meta['lang_type']}"
            if meta.get("lang_code"):
                lang_info += f"/{meta['lang_code']}"
            lang_info += "]"

        block = (
            f"[{i}] {header}"
            + (f" ({tier_label})" if tier_label else "")
            + lang_info
            + f"\n{doc.page_content}"
        )

        block_tokens = _estimate_tokens(block)
        if running_tokens + block_tokens > max_context_tokens and parts:
            # Already have at least one doc — stop adding more
            break
        parts.append(block)
        running_tokens += block_tokens

    return "\n\n".join(parts)
