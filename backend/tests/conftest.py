import pytest
from fastapi.testclient import TestClient

from app.ai.cache import InMemoryResultCache
from app.ai.client import AIClient, get_ai_client
from app.ai.provider import NullProvider
from app.core.config import Settings, get_settings
from app.main import create_app

RESUME_TEXT = """Karthik Mathappan
karthik@example.com | +91 98765 43210 | linkedin.com/in/example

SUMMARY
Backend engineer focused on Python APIs and data pipelines.

EXPERIENCE
Senior Backend Engineer, Acme Corp    Jun 2021 - Present
- Cut p95 API latency by 42% by introducing request-level caching
- Led migration of 14 services from Flask to FastAPI
- Responsible for on-call rotation and incident response

Backend Engineer, Globex    Jul 2018 - May 2021
- Built an ingestion pipeline processing 2M events per day
- Mentored three junior engineers

EDUCATION
B.E. Computer Science, Anna University, 2018

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS, Redis, pytest
"""


@pytest.fixture
def settings() -> Settings:
    # AI is deliberately off: every test here must pass without a network call
    # or an API key. AI-dependent behaviour is tested with fakes instead.
    return Settings(
        environment="development",
        ai_provider="null",
        anthropic_api_key="",
        cors_origins="http://localhost:3000",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """A test client wired to test settings and a disabled AI provider.

    The dependency overrides matter: without them these tests would read the
    developer's real `.env`, and would start passing or failing depending on
    whether an API key happened to be present.
    """
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_ai_client] = lambda: AIClient(
        NullProvider(), settings, InMemoryResultCache()
    )
    return TestClient(app)


@pytest.fixture
def resume_bytes() -> bytes:
    return RESUME_TEXT.encode("utf-8")
