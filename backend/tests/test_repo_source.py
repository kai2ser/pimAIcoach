"""
Tests for the repo_source module — JOIN query and country name caching.
"""

from unittest.mock import patch, MagicMock

from app.ingestion.repo_source import resolve_country_name


class TestResolveCountryName:
    """Tests for resolve_country_name with caching."""

    def test_resolves_known_country(self):
        """Returns country name for a valid ISO3 code."""
        resolve_country_name.cache_clear()  # Reset lru_cache

        with patch("app.ingestion.repo_source.psycopg") as mock_psycopg:
            mock_conn = MagicMock()
            mock_psycopg.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_psycopg.connect.return_value.__exit__ = MagicMock(return_value=False)

            mock_cur = MagicMock()
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mock_cur.fetchone.return_value = ("Colombia",)

            result = resolve_country_name("COL")
            assert result == "Colombia"

    def test_returns_input_when_not_found(self):
        """Falls back to the input string if ISO3 not in DB."""
        resolve_country_name.cache_clear()

        with patch("app.ingestion.repo_source.psycopg") as mock_psycopg:
            mock_conn = MagicMock()
            mock_psycopg.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_psycopg.connect.return_value.__exit__ = MagicMock(return_value=False)

            mock_cur = MagicMock()
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mock_cur.fetchone.return_value = None

            result = resolve_country_name("ZZZ")
            assert result == "ZZZ"

    def test_cache_prevents_repeated_db_calls(self):
        """Second call for same country should use cache, not DB."""
        resolve_country_name.cache_clear()

        with patch("app.ingestion.repo_source.psycopg") as mock_psycopg:
            mock_conn = MagicMock()
            mock_psycopg.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_psycopg.connect.return_value.__exit__ = MagicMock(return_value=False)

            mock_cur = MagicMock()
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mock_cur.fetchone.return_value = ("Kenya",)

            # First call — hits DB
            result1 = resolve_country_name("KEN")
            # Second call — should use cache
            result2 = resolve_country_name("KEN")

            assert result1 == "Kenya"
            assert result2 == "Kenya"
            # psycopg.connect should only have been called once
            assert mock_psycopg.connect.call_count == 1
