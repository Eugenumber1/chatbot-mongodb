.PHONY: run test down build clean

run:
	docker compose up -d --build

test:
	docker compose run --rm app pytest

down:
	docker compose down

build:
	docker build --no-cache --progress=plain -t mongodb-chatbot .

clean:
	docker compose down -v
	docker system prune -f