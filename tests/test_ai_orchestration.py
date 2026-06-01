import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import PromptTemplate, AIMemory


@pytest.mark.asyncio
async def test_create_prompt_template(client: AsyncClient, db_session: AsyncSession) -> None:
    payload = {
        "name": "test_prompt",
        "description": "A test prompt template",
        "system_prompt": "You are a helpful assistant.",
        "is_active": True,
    }

    response = await client.post("/api/v1/ai/prompts", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "test_prompt"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_prompt_templates(client: AsyncClient, db_session: AsyncSession) -> None:
    # Seed a template
    template = PromptTemplate(
        name="list_prompt",
        description="For listing",
        system_prompt="Do list things.",
    )
    db_session.add(template)
    await db_session.commit()

    response = await client.get("/api/v1/ai/prompts")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 1
    assert any(p["name"] == "list_prompt" for p in data)


@pytest.mark.asyncio
async def test_chat_stream_mock_fallback(client: AsyncClient) -> None:
    """Test the Vercel AI SDK formatted streaming response endpoint."""
    payload = {"message": "Hello"}

    # We don't have a real Gemini API key in the test environment, so it will fall back to mock
    # and return a Vercel formatted stream.
    response = await client.post("/api/v1/ai/chat", json=payload)

    assert response.status_code == 200
    assert response.headers.get("x-vercel-ai-data-stream") == "v1"

    content = response.text
    # Expecting the fallback mock message format
    assert content.startswith("0:")
    assert "mock fallback response" in content
