# Form-filling Insurance AI-agent with Session and Record stoarge in MongoDB

## How to Test?
Clone the repository to your local machine. Then, copy `.env.example` to `.env` and change the values of the keys. 
To execute the tests please run `make test` command. It will create docker containers with application and database services and run the tests inside.
There are 20 tests total, and if all of them are passing - you will see a corresponding message in the terminal. Tests cover the Database and App functionality as well as 2 end-to-end scenarios. The scenarios are the following:
1. The user is giving their information and there are no duplicate licence plate found.
2. There is a duplicate licence plate found.

## How to Run?
Next, run `make run` from the root of the project. This command will build the docker images of the FastAPI backend and MongoDB instance and deploy them locally. Make sure your docker desktop app is open before you run it.
You can later try FastAPI swagger by navigating to `https://localhost:8000/docs`. You can send a `post` request to the /chat endpoint. The first message can be without any session id. 
App will see that there is a new session initiated and will create a new session id and send it in the response to the user. Please, copy that session id and paste to the body of your next request to continue the conversation. The chatbot follows the flow of conversation to gather necessary information from the user and asks relevant questions.
