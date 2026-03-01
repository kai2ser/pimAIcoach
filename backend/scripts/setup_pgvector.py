"""
Enable pgvector extension and create the LangChain vector store table on Neon.

Usage:
    python -m scripts.setup_pgvector

Requires PIM_DATABASE_URL in .env or environment.
"""

import psycopg

from app.config import settings


def setup():
    print(f"Connecting to database...")

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # Enable pgvector extension
            print("Enabling pgvector extension...")
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            print("pgvector extension enabled.")

            # Verify
            cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            row = cur.fetchone()
            if row:
                print(f"pgvector version: {row[0]}")
            else:
                print("WARNING: pgvector extension not found after creation!")
                return

            # Check if langchain collection table already exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'langchain_pg_collection'
                );
            """)
            exists = cur.fetchone()[0]

            if exists:
                print("LangChain PGVector tables already exist.")
            else:
                print("LangChain PGVector tables will be auto-created on first use.")

    print("Setup complete.")


if __name__ == "__main__":
    setup()
