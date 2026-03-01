"""
Tests for metadata filter construction.
"""

from app.retrieval.filters import build_metadata_filter, parse_filter_params


class TestBuildMetadataFilter:
    """Tests for build_metadata_filter()."""

    def test_empty_input(self):
        assert build_metadata_filter({}) == {}

    def test_simple_equality(self):
        result = build_metadata_filter({"country": "COL"})
        assert result == {"country": "COL"}

    def test_multiple_equality(self):
        result = build_metadata_filter({"country": "COL", "policy_guidance_tier": 3})
        assert result == {"country": "COL", "policy_guidance_tier": 3}

    def test_list_filter(self):
        result = build_metadata_filter({"country": ["COL", "KEN"]})
        assert result == {"country": {"$in": ["COL", "KEN"]}}

    def test_range_operator_passthrough(self):
        result = build_metadata_filter({"year": {"$gte": 2020}})
        assert result == {"year": {"$gte": 2020}}

    def test_year_from_only(self):
        result = build_metadata_filter({"year_from": 2020})
        assert result == {"year": {"$gte": 2020}}

    def test_year_to_only(self):
        result = build_metadata_filter({"year_to": 2025})
        assert result == {"year": {"$lte": 2025}}

    def test_year_from_and_to(self):
        result = build_metadata_filter({"year_from": 2020, "year_to": 2025})
        assert result == {"year": {"$gte": 2020, "$lte": 2025}}

    def test_year_from_with_other_filters(self):
        result = build_metadata_filter({"country": "COL", "year_from": 2020})
        assert result == {"country": "COL", "year": {"$gte": 2020}}

    def test_unknown_fields_dropped(self):
        result = build_metadata_filter({"country": "COL", "unknown_field": "value"})
        assert result == {"country": "COL"}

    def test_all_valid_fields(self):
        filters = {
            "country": "COL",
            "country_name": "Colombia",
            "policy_guidance_tier": 1,
            "strategy_tier": 2,
            "year": 2020,
            "source": "National Treasury",
            "lang_type": "ENG",
            "record_id": "REC-001",
        }
        result = build_metadata_filter(filters)
        assert result == filters


class TestParseFilterParams:
    """Tests for parse_filter_params()."""

    def test_no_params(self):
        assert parse_filter_params() is None

    def test_country_only(self):
        result = parse_filter_params(country="COL")
        assert result == {"country": "COL"}

    def test_year_range(self):
        result = parse_filter_params(year_from=2020, year_to=2025)
        assert result == {"year": {"$gte": 2020, "$lte": 2025}}

    def test_year_from_only(self):
        result = parse_filter_params(year_from=2020)
        assert result == {"year": {"$gte": 2020}}

    def test_combined(self):
        result = parse_filter_params(country="COL", tier=1, lang="ENG")
        assert result == {"country": "COL", "policy_guidance_tier": 1, "lang_type": "ENG"}
