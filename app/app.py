from fastapi import FastAPI
from .sessions import *
from .models import ChatResponse, ChatRequest
from .insurance_agent import InsuranceAgent
import dotenv
import json
from .db import sessions, records
from .service_exceptions import *

dotenv.load_dotenv()


insurance_agent = InsuranceAgent()

app = FastAPI(title="Insurance AI App")


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    global insurance_agent
    if chat_request.session_id:
        session_id, history = await get_or_create_session(
            sessions=sessions, session_id=chat_request.session_id
        )
    else:
        session_id, history = await get_or_create_session(sessions=sessions)
    history.append(Message(role="user", content=chat_request.message))
    message_history = [Message.model_validate(h) for h in history]
    agent_response = await insurance_agent.respond(history=message_history)
    if agent_response:
        message_history.append(Message(role="assistant", content=agent_response))
        agent_response_dict = json.loads(agent_response)
        licence_plate_number = agent_response_dict.get("licence_plate_number")
        if licence_plate_number:
            duplicate = await detect_duplicate(records, licence_plate_number)
            if duplicate:
                reply = f"There is already a record for licence plate {agent_response_dict["licence_plate_number"]}. Please check if you entered the correct details."
                message_history.append(Message(role="assistant", content=reply))
                complete = False
        if agent_response_dict.get("complete"):
            data = agent_response_dict
            plate = agent_response_dict.get("licence_plate_number")

            data["session_id"] = session_id
            await save_record(
                records, plate, data, prompt=insurance_agent.system_prompt
            )
            reply = "Thank you for providing all the necessary information. Here is your insurance quota..."
            complete = True
        else:
            reply = agent_response_dict.get("next_question")
            complete = False

        await update_session(sessions, session_id=session_id, history=message_history)
        return ChatResponse(
            session_id=session_id, agent_response=reply, complete=complete
        )
    else:
        return ChatResponse(
            session_id=session_id,
            agent_response="The Agent is unavailable at the moment",
            complete=False,
        )
