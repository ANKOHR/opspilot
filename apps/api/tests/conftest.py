from __future__ import annotations

import pytest
from opspilot_api.database import Base
from opspilot_api.repository import Repository
from opspilot_api.runtime import WorkflowRuntime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def runtime(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = Repository(sessions)
    repository.seed_demo()
    return WorkflowRuntime(repository), repository
