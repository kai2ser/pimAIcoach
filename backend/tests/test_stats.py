"""
Tests for the statistics endpoints: /api/stats and /api/stats/detail.
"""

from unittest.mock import patch, MagicMock


class TestStatsEndpoint:
    """Tests for GET /api/stats."""

    def test_stats_no_auth_required(self, client):
        """Stats endpoint is public."""
        with patch("app.api.stats._get_pg_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)

            # Mock collection UUID lookup
            mock_conn.execute.return_value.fetchone.return_value = None

            response = client.get("/api/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_chunks" in data
            assert "total_documents" in data
            assert "collection_name" in data

    def test_stats_empty_collection(self, client):
        """Returns zeros when collection doesn't exist."""
        with patch("app.api.stats._get_pg_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)

            # No collection found
            mock_conn.execute.return_value.fetchone.return_value = None

            # Clear cache to force re-fetch
            from app.api.stats import invalidate_stats_cache
            invalidate_stats_cache()

            response = client.get("/api/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["total_chunks"] == 0
            assert data["total_documents"] == 0


class TestStatsDetailEndpoint:
    """Tests for GET /api/stats/detail."""

    def test_stats_detail_no_auth_required(self, client):
        """Stats detail endpoint is public."""
        with patch("app.api.stats._get_pg_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)

            mock_conn.execute.return_value.fetchone.return_value = None

            from app.api.stats import invalidate_stats_cache
            invalidate_stats_cache()

            response = client.get("/api/stats/detail")
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "by_country" in data
            assert "by_tier" in data
            assert "by_year" in data
            assert "embedding_model" in data
            assert "vector_store" in data

    def test_stats_detail_empty_collection(self, client):
        """Returns empty breakdowns when collection doesn't exist."""
        with patch("app.api.stats._get_pg_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)

            mock_conn.execute.return_value.fetchone.return_value = None

            from app.api.stats import invalidate_stats_cache
            invalidate_stats_cache()

            response = client.get("/api/stats/detail")
            data = response.json()
            assert data["summary"]["total_chunks"] == 0
            assert data["by_country"] == []
            assert data["by_tier"] == []
            assert data["by_year"] == []


class TestStatsCache:
    """Tests for stats cache invalidation."""

    def test_invalidate_stats_cache(self):
        from app.api.stats import _cache, _detail_cache, invalidate_stats_cache

        # Simulate cached data
        _cache["data"] = {"test": True}
        _cache["expires_at"] = 99999999999.0
        _detail_cache["data"] = {"test": True}
        _detail_cache["expires_at"] = 99999999999.0

        invalidate_stats_cache()

        assert _cache["data"] is None
        assert _cache["expires_at"] == 0.0
        assert _detail_cache["data"] is None
        assert _detail_cache["expires_at"] == 0.0
