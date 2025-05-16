from datetime import datetime
from app.sessions import (
    get_or_create_session,
    update_session,
    detect_duplicate,
    save_record,
)
from app.models import Message
import mongomock_motor


async def test_mock_client():
    collection = mongomock_motor.AsyncMongoMockClient()["tests"]["test-1"]

    assert await collection.find({}).to_list(None) == []

    result = await collection.insert_one({"a": 1})
    assert result.inserted_id

    assert len(await collection.find({}).to_list(None)) == 1


async def test_get_or_create_session_new():
    sessions = mongomock_motor.AsyncMongoMockClient()["chatbot"]["sessions"]
    session_id, history = await get_or_create_session(sessions=sessions)

    assert isinstance(session_id, str)
    assert len(session_id) > 0
    assert isinstance(history, list)
    assert len(history) == 0

    session = await sessions.find_one({"_id": session_id})
    assert session is not None
    assert session["history"] == []
    assert isinstance(session["created_at"], datetime)


async def test_get_or_create_session_existing():
    sessions = mongomock_motor.AsyncMongoMockClient()["chatbot"]["sessions"]
    session_id, _ = await get_or_create_session(sessions)
    retrieved_id, history = await get_or_create_session(sessions, session_id)

    assert retrieved_id == session_id
    assert isinstance(history, list)


async def test_update_session():
    sessions = mongomock_motor.AsyncMongoMockClient()["chatbot"]["sessions"]
    session_id, _ = await get_or_create_session(sessions)
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there"),
    ]

    await update_session(sessions, session_id, messages)

    session = await sessions.find_one({"_id": session_id})
    assert session is not None
    assert len(session["history"]) == 2
    assert session["history"][0]["role"] == "user"
    assert session["history"][0]["content"] == "Hello"
    assert isinstance(session["updated_at"], datetime)


async def test_detect_duplicate_true():
    records = mongomock_motor.AsyncMongoMockClient()["chatbot"]["records"]
    licence_plate = "ABC123"
    test_data = {
        "licence_plate": licence_plate,
        "form_data": {
            "key": "value",
            "another_key": True,
        },
        "prompt_used": "test prompt",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    await records.insert_one(test_data)
    result = await detect_duplicate(records, licence_plate)
    assert result is True


async def test_detect_duplicate_false():
    records = mongomock_motor.AsyncMongoMockClient()["chatbot"]["records"]
    result = await detect_duplicate(records, "NONEXISTENT")
    assert result is False


async def test_save_record():
    records = mongomock_motor.AsyncMongoMockClient()["chatbot"]["records"]
    licence_plate = "XYZ789"
    data = {
        "name": "John Doe",
        "is_valid": True,
    }
    prompt = "test prompt"

    await save_record(records, licence_plate, data, prompt)

    record = await records.find_one({"licence_plate": licence_plate})
    assert record is not None
    assert record["licence_plate"] == licence_plate
    assert record["form_data"] == data
    assert record["prompt_used"] == prompt
