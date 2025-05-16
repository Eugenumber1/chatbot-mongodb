from typing import Dict, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Record(BaseModel):
    licence_plate: str
    form_data: Dict[str, Union[str, bool]]
    prompt_used: str
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())


class ChatRequest(BaseModel):
    session_id: str | None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    agent_response: str
    complete: bool


class CarInfo(BaseModel):
    reasoning: str
    next_question: str
    car_type: Literal["Sedan", "Coupe", "Station Wagon", "Hatchback", "Minivan"]
    licence_plate_number: str
    manufacturer_or_brand: str
    year_of_construction: str
    complete: bool
    birthdate: str
    name: str


class Message(BaseModel):
    role: str
    content: str
