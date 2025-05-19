from litellm import acompletion
import dotenv
import os
import logging
from .config.config import Config
from .models import Message, CarInfo
import asyncio
from .service_exceptions import AgentNotAvailable


dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class InsuranceAgent:
    def __init__(self):
        self.config = Config()
        self.model = self.config.model_name
        self.system_prompt = self.config.system_prompt

    async def respond(self, history: list[Message]) -> str | None:
        try:
            response = await self.generate_answer(history=history)
            return response
        except Exception as e:
            logging.error(
                "The following error happened while generating the response: ", e
            )
            raise AgentNotAvailable("The agent is not available")

    async def generate_answer(self, history: list[Message]):
        messages = [{"role": "system", "content": self.system_prompt}] + [
            h.model_dump() for h in history
        ]
        api_response = await acompletion(
            self.model, messages=messages, response_format=CarInfo
        )
        return api_response.choices[0].message.content  # type: ignore


if __name__ == "__main__":
    i_a = InsuranceAgent()

    async def main():
        response = await i_a.respond(
            history=[
                Message(
                    role="user",
                    content="Hey there, I have a minivan toyota car, it's number plate is 567-78AA, year of construction is 2021. My name is Zhenya, I was born 1959-12-20",
                )
            ]
        )
        if response:
            print(response)

    asyncio.run(main())
