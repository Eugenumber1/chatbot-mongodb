import pytest
from app.app import app
from unittest.mock import patch, AsyncMock
import json
from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture
def mock_insurance_agent():
    with patch("app.app.insurance_agent") as mock_agent:
        mock_agent.respond = AsyncMock()
        mock_agent.system_prompt = "test prompt"
        mock_agent.respond.side_effect = [
            json.dumps({"next_question": "What is your name?", "complete": False}),
            json.dumps(
                {
                    "name": "John Doe",
                    "next_question": "What is your car's license plate number?",
                    "complete": False,
                }
            ),
            json.dumps(
                {
                    "name": "John Doe",
                    "licence_plate_number": "ABC123",
                    "car_type": "Sedan",
                    "manufacturer_or_brand": "Toyota",
                    "year_of_construction": "2020",
                    "birthdate": "1990-01-01",
                    "complete": True,
                }
            ),
        ]
        yield mock_agent


@pytest.fixture
async def test_db():

    mongo_uri = "mongodb://user:password@mongodb_test:27017"
    client = AsyncIOMotorClient(mongo_uri)
    db = client["chatbot_test"]

    with (
        patch("app.db.client", client),
        patch("app.db.db", db),
        patch("app.db.sessions", db.sessions),
        patch("app.db.records", db.records),
    ):
        yield db
        await client.drop_database("chatbot_test")
        client.close()


@pytest.mark.asyncio
async def test_complete_conversation_flow(async_client, test_db, mock_insurance_agent):
    response = await async_client.post(
        "/chat", json={"session_id": None, "message": "hello"}
    )
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    # assert data["agent_response"] == "What is your name?"
    assert not data["complete"]
    response = await async_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "My name is John Doe, I have toyota minivan 2023 year of construction. I was born 08-05-2002",
        },
    )
    assert response.status_code == 200
    data = response.json()
    # assert data["agent_response"] == "What is your car's license plate number?"
    assert not data["complete"]

    response = await async_client.post(
        "/chat",
        json={"session_id": session_id, "message": "My license plate is ABC123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert (
        data["agent_response"]
        == "Thank you for providing all the necessary information. Here is your insurance quota..."
    )
    assert data["complete"]

    record = await test_db.records.find_one({"licence_plate": "ABC123"})
    assert record is not None
    assert record["form_data"]["name"] == "John Doe"
    assert record["form_data"]["licence_plate_number"] == "ABC123"
    assert record["form_data"]["car_type"] == "Sedan"
    assert record["form_data"]["manufacturer_or_brand"] == "Toyota"
    assert record["form_data"]["year_of_construction"] == "2020"
    assert record["prompt_used"] == "test prompt"


@pytest.mark.asyncio
async def test_duplicate_license_plate(async_client, mock_insurance_agent, test_db):

    mock_insurance_agent.respond.side_effect = [
        json.dumps({"next_question": "What is your name?", "complete": False}),
        json.dumps(
            {
                "name": "User1",
                "next_question": "What is your car's license plate number?",
                "complete": False,
            }
        ),
        json.dumps(
            {
                "name": "User1",
                "licence_plate_number": "ABC123",
                "car_type": "Sedan",
                "manufacturer_or_brand": "Toyota",
                "year_of_construction": "2020",
                "birthdate": "1990-01-01",
                "complete": True,
            }
        ),
        json.dumps({"next_question": "What is your name?", "complete": False}),
        json.dumps(
            {
                "name": "User2",
                "next_question": "What is your car's license plate number?",
                "complete": False,
            }
        ),
        json.dumps(
            {
                "name": "User2",
                "licence_plate_number": "ABC123",  # duplicate licence plt
                "car_type": "Coupe",
                "manufacturer_or_brand": "Honda",
                "year_of_construction": "2021",
                "birthdate": "1985-05-05",
                "complete": False,
            }
        ),
    ]

    resp1 = await async_client.post(
        "/chat", json={"session_id": None, "message": "hello"}
    )
    sid1 = resp1.json()["session_id"]
    await async_client.post(
        "/chat", json={"session_id": sid1, "message": "Name is User1"}
    )
    await async_client.post(
        "/chat", json={"session_id": sid1, "message": "Plate is ABC123"}
    )
    resp2 = await async_client.post(
        "/chat", json={"session_id": None, "message": "hello"}
    )
    assert resp2.status_code == 200
    sid2 = resp2.json()["session_id"]
    await async_client.post(
        "/chat", json={"session_id": sid2, "message": "Name is User2"}
    )
    dup_resp = await async_client.post(
        "/chat", json={"session_id": sid2, "message": "Plate is ABC123"}
    )
    assert dup_resp.status_code == 200
    dup_data = dup_resp.json()
    assert (
        dup_data["agent_response"]
        == "There is already a record for licence plate ABC123. Please check if you entered the correct details."
    )
    assert dup_data["complete"] is False
    count = await test_db.records.count_documents({"licence_plate": "ABC123"})
    assert count == 1
