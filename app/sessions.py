import uuid
from datetime import datetime
from .models import Message, Record
from typing import List, Union
import logging
from pymongo.errors import PyMongoError


async def get_or_create_session(sessions, session_id: Union[str, None] = None):
    try:
        if session_id:
            try:
                session = await sessions.find_one({"_id": session_id})
            except PyMongoError as e:
                logging.error(f"Database error during find_one: {e}")
                raise
            if session:
                return session_id, session["history"]
            else:
                logging.info(
                    f"Requested non-existent session with id {session_id}. Creating a new one instead."
                )

        new_id = str(uuid.uuid4())
        try:
            await sessions.insert_one(
                {"_id": new_id, "history": [], "created_at": datetime.now()}
            )
        except PyMongoError as e:
            logging.error(f"Database error during insert_one: {e}")
            raise
        return new_id, []
    except Exception as e:
        logging.error(f"Unexpected error in get_or_create_session: {e}")
        raise


async def update_session(sessions, session_id: str, history: List[Message]):
    try:
        await sessions.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "history": [h.model_dump() for h in history],
                    "updated_at": datetime.now(),
                }
            },
        )
    except PyMongoError as e:
        logging.error(f"Database error during update_one: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in update_session: {e}")
        raise


async def detect_duplicate(records, licence_plate: str) -> bool:
    try:
        existing = await records.find_one({"licence_plate": licence_plate})
        return existing is not None
    except PyMongoError as e:
        logging.error(f"Database error during find_one in detect_duplicate: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in detect_duplicate: {e}")
        raise


async def save_record(records, licence_plate: str, data: dict, prompt: str):
    try:
        rec = Record(licence_plate=licence_plate, form_data=data, prompt_used=prompt)
        await records.insert_one(rec.model_dump())
    except PyMongoError as e:
        logging.error(f"Database error during insert_one in save_record: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in save_record: {e}")
        raise
