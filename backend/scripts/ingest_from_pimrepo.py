"""
Ingest documents from the pimrepository Neon database into the RAG vector store.

Connects to the same Neon PostgreSQL used by pimrepository, fetches all
policy_records with their documents, downloads PDFs from Vercel Blob,
and runs them through the ingestion pipeline.

Usage:
    python -m scripts.ingest_from_pimrepo                  # ingest all
    python -m scripts.ingest_from_pimrepo --country COL    # ingest one country
    python -m scripts.ingest_from_pimrepo --record-id abc  # ingest one record
    python -m scripts.ingest_from_pimrepo --dry-run        # preview without ingesting

Requires PIM_DATABASE_URL in .env pointing to the pimrepository Neon DB.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.config import settings
from app.ingestion.metadata import PolicyMetadata
from app.ingestion.pipeline import ingest_document
from app.ingestion.repo_source import fetch_records_with_docs, resolve_country_name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ingest")


async def ingest_records(
    records: list[dict],
    chunker_strategy: str | None = None,
    dry_run: bool = False,
) -> None:
    """Process and ingest all records into the vector store."""
    total_docs = sum(len(r["documents"]) for r in records)
    logger.info(
        "Found %d records with %d documents total", len(records), total_docs
    )

    if total_docs == 0:
        logger.warning("No documents found to ingest. Records may not have uploaded PDFs yet.")
        return

    success = 0
    failed = 0

    for record in records:
        if not record["documents"]:
            logger.info(
                "Skipping %s — %s (no documents attached)",
                record["country"],
                record["name_eng"],
            )
            continue

        country_name = resolve_country_name(record["country"])

        for doc in record["documents"]:
            doc_label = (
                f"{record['country']} — {record['name_eng']} ({doc['lang_type']})"
            )

            if dry_run:
                logger.info("[DRY RUN] Would ingest: %s", doc_label)
                logger.info(
                    "  URL: %s | Size: %s bytes",
                    doc["blob_url"][:80] + "..." if len(doc["blob_url"]) > 80 else doc["blob_url"],
                    doc.get("file_size", "unknown"),
                )
                continue

            logger.info("Ingesting: %s", doc_label)

            try:
                metadata = PolicyMetadata(
                    record_id=str(record["id"]),
                    country=record["country"],
                    country_name=country_name,
                    name_eng=record["name_eng"],
                    name_orig=record.get("name_orig"),
                    year=record.get("year"),
                    year_revised=record.get("year_revised"),
                    source=record.get("source"),
                    policy_guidance_tier=record.get("policy_guidance_tier"),
                    strategy_tier=record.get("strategy_tier"),
                    lang_type=doc["lang_type"],
                    lang_code=doc.get("lang_code"),
                    overview=record.get("overview"),
                    link=record.get("link"),
                    pages=record.get("pages"),
                    tokens=record.get("tokens"),
                )

                result = await ingest_document(
                    metadata=metadata,
                    source=doc["blob_url"],
                    filename=doc.get("file_name"),
                    chunker_strategy=chunker_strategy,
                )

                logger.info(
                    "  -> %d chunks created for %s",
                    result.chunks_created,
                    doc_label,
                )
                success += 1

            except Exception:
                logger.exception("  -> FAILED to ingest %s", doc_label)
                failed += 1

    logger.info(
        "Ingestion complete: %d succeeded, %d failed out of %d documents",
        success,
        failed,
        total_docs,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Ingest PIM documents from the pimrepository database"
    )
    parser.add_argument(
        "--country",
        help="Filter by country (ISO3 code or name)",
    )
    parser.add_argument(
        "--record-id",
        help="Ingest a single record by UUID",
    )
    parser.add_argument(
        "--chunker",
        choices=["recursive", "semantic", "by_section"],
        help="Override the chunking strategy",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be ingested without actually doing it",
    )
    args = parser.parse_args()

    if not settings.database_url:
        logger.error("PIM_DATABASE_URL not set. Check your .env file.")
        sys.exit(1)

    records = fetch_records_with_docs(
        country=args.country,
        record_id=args.record_id,
    )

    asyncio.run(
        ingest_records(
            records,
            chunker_strategy=args.chunker,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
