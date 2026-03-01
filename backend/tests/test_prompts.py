"""
Tests for prompt formatting utilities.
"""

from langchain_core.documents import Document

from app.generation.prompts import format_documents


class TestFormatDocuments:
    """Tests for format_documents()."""

    def test_empty_list(self):
        assert format_documents([]) == ""

    def test_single_doc_with_full_metadata(self):
        doc = Document(
            page_content="Public investment law text...",
            metadata={
                "country_name": "Colombia",
                "name_eng": "Public Investment Framework",
                "year": 2020,
                "policy_guidance_tier": 1,
            },
        )
        result = format_documents([doc])

        assert "[1]" in result
        assert "Colombia" in result
        assert "Public Investment Framework" in result
        assert "2020" in result
        assert "Legislation" in result
        assert "Public investment law text..." in result

    def test_tier_labels(self):
        tiers = {1: "Legislation", 2: "Regulation", 3: "Guidelines", 4: "Strategy"}
        for tier_num, label in tiers.items():
            doc = Document(
                page_content="text",
                metadata={"policy_guidance_tier": tier_num},
            )
            result = format_documents([doc])
            assert label in result

    def test_doc_with_missing_metadata(self):
        doc = Document(page_content="Some text", metadata={})
        result = format_documents([doc])

        assert "[1]" in result
        assert "Document 1" in result
        assert "Some text" in result

    def test_multiple_docs(self):
        docs = [
            Document(
                page_content="First doc",
                metadata={"country_name": "Colombia", "year": 2020},
            ),
            Document(
                page_content="Second doc",
                metadata={"country_name": "Kenya", "year": 2021},
            ),
        ]
        result = format_documents(docs)

        assert "[1]" in result
        assert "[2]" in result
        assert "Colombia" in result
        assert "Kenya" in result

    def test_country_code_fallback(self):
        doc = Document(
            page_content="text",
            metadata={"country": "COL"},
        )
        result = format_documents([doc])
        assert "COL" in result
