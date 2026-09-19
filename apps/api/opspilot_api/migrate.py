from __future__ import annotations

import os

from alembic import command
from alembic.config import Config


def main() -> None:
    config = Config(os.getenv("ALEMBIC_CONFIG", "alembic.ini"))
    command.upgrade(config, "head")
    print("OpsPilot database migration complete")


if __name__ == "__main__":
    main()
