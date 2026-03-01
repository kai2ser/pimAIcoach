"""
Tests for metadata enrichment.
"""

from langchain_core.documents import Document

from app.ingestion.metadata import PolicyMetadata, enrich_chunks, _metadata_to_dict


class TestMetadataToDict:
    """Tests for _metadata_to_dict()."""

    def test_drops_none_values(self):
        meta = PolicyMetadata(record_id="REC-001", country="COL")
        result = _metadata_to_dict(meta)
        assert result == {"record_id": "REC-001", "country": "COL"}
        assert "year" not in result
        assert "name_eng" not in result

    def test_includes_all_set_fields(self):
        meta = PolicyMetadata(
            record_id="REC-002",
            country="KEN",
            country_name="Kenya",
            year=2021,
            policy_guidance_tier=2,
            lang_type="ENG",
        )
        result = _metadata_to_dict(meta)
        assert result == {
            "record_id": "REC-002",
            "country": "KEN",
            "country_name": "Kenya",
            "year": 2021,
            "policy_guidance_tier": 2,
            "lang_type": "ENG",
        }


class TestEnrichChunks:
    """Tests for enrich_chunks()."""

    def test_attaches_metadata_to_chunks(self):
        chunks = [
            Document(page_content="Chunk 1"),
            Document(page_content="Chunk 2"),
        ]
        meta = PolicyMetadata(record_id="REC-001", country="COL", year=2020)
        result = enrich_chunks(chunks, meta)

        assert len(result) == 2
        for chunk in result:
            assert chunk.metadata["record_id"] == "REC-001"
            assert chunk.metadata["country"] == "COL"
            assert chunk.metadata["year"] == 2020

    def test_sets_total_chunks(self):
        chunks = [
            Document(page_content="A"),
            Document(page_content="B"),
            Document(page_content="C"),
        ]
        meta = PolicyMetadata(record_id="REC-001", country="COL")
        result = enrich_chunks(chunks, meta)

        for chunk in result:
            assert chunk.metadata["total_chunks"] == 3

    def test_preserves_existing_metadata(self):
        chunks = [Document(page_content="Text", metadata={"page": 5})]
        meta = PolicyMetadata(record_id="REC-001", country="COL")
        result = enrich_chunks(chunks, meta)

        assert result[0].metadata["page"] == 5
        assert result[0].metadata["country"] == "COL"
