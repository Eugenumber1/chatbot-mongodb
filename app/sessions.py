import uuid
from datetime import datetime
from .models import Message, Record
from typing import List, Union


async def get_or_create_session(sessions, session_id: Union[str, None] = None):
    if session_id:
        session = await sessions.find_one({"_id": session_id})
        if session:
            return session_id, session["history"]
    new_id = str(uuid.uuid4())
    await sessions.insert_one(
        {"_id": new_id, "history": [], "created_at": datetime.now()}
    )
    return new_id, []


async def update_session(sessions, session_id: str, history: List[Message]):
    await sessions.update_one(
        {"_id": session_id},
        {
            "$set": {
                "history": [h.model_dump() for h in history],
                "updated_at": datetime.now(),
            }
        },
    )


async def detect_duplicate(records, licence_plate: str) -> bool:
    existing = await records.find_one({"licence_plate": licence_plate})
    return existing is not None


async def save_record(records, licence_plate: str, data: dict, prompt: str):
    rec = Record(licence_plate=licence_plate, form_data=data, prompt_used=prompt)
    await records.insert_one(rec.model_dump())
