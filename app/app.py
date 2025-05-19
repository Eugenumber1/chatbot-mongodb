from fastapi import FastAPI, HTTPException, status
from .sessions import *
from .models import ChatResponse, ChatRequest
from .insurance_agent import InsuranceAgent
import dotenv
import json
from . import db
from .service_exceptions import *
from pymongo.errors import PyMongoError
from typing import Optional
import logging

dotenv.load_dotenv()

insurance_agent = InsuranceAgent()
app = FastAPI(title="Insurance AI App")


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    global insurance_agent
    session_id: Optional[str] = None
    message_history: List[Message] = []
    duplicate = False
    try:
        if chat_request.session_id:
            session_id, history = await get_or_create_session(
                sessions=db.sessions, session_id=chat_request.session_id
            )
        else:
            session_id, history = await get_or_create_session(sessions=db.sessions)

        message_history = [Message.model_validate(h) for h in history]
        message_history.append(Message(role="user", content=chat_request.message))
        try:
            agent_response = await insurance_agent.respond(history=message_history)
        except AgentNotAvailable as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent is temporarily unavailable",
            )

        if not agent_response:
            return ChatResponse(
                session_id=session_id,
                agent_response="The Agent is unavailable at the moment",
                complete=False,
            )
        try:
            message_history.append(Message(role="assistant", content=agent_response))
            agent_response_dict = json.loads(agent_response)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing agent response",
            )
        licence_plate_number = agent_response_dict.get("licence_plate_number")
        complete = False
        reply = None

        if licence_plate_number:
            duplicate = await detect_duplicate(db.records, licence_plate_number)
            if duplicate:
                reply = f"There is already a record for licence plate {licence_plate_number}. Please check if you entered the correct details."
                message_history.append(Message(role="assistant", content=reply))
                complete = False

        if agent_response_dict.get("complete"):
            data = agent_response_dict
            plate = agent_response_dict.get("licence_plate_number")
            data["session_id"] = session_id

            await save_record(
                db.records, plate, data, prompt=insurance_agent.system_prompt
            )
            reply = "Thank you for providing all the necessary information. Here is your insurance quota..."
            complete = True
        else:
            if not duplicate:
                reply = agent_response_dict.get("next_question")
            if not reply:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid agent response format",
                )

        await update_session(
            db.sessions, session_id=session_id, history=message_history
        )

        return ChatResponse(
            session_id=session_id, agent_response=reply, complete=complete
        )

    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is temporarily unavailable",
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
