#!/usr/bin/env python3
"""
scripts/init_db.py
───────────────────
Create all PostgreSQL tables from SQLAlchemy models.
Run this once after starting the DB container:

  docker-compose exec backend python scripts/init_db.py
  # OR locally:
  python scripts/init_db.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.base_class import Base
from app.db.session import engine
import app.db.base  # noqa: F401 – triggers model imports


def main():
    print("Creating database tables…")
    Base.metadata.create_all(bind=engine)
    print("Done ✓")


if __name__ == "__main__":
    main()
