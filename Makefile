include .env

DOCKER_COMPOSE=docker compose
DOCKER_COMPOSE_RUN=$(DOCKER_COMPOSE) run --rm bot

build:
	$(DOCKER_COMPOSE) build --parallel

up: build
	$(DOCKER_COMPOSE) up


restart_bot:
	docker compose up -d --build bot

lint:
	uv run pre-commit run --all-files

format:
	uv run isort .
	uv run black .

flake:
	flake8 --per-file-ignores="__init__.py:F401" --ignore E203,E501,W503 src tests bot.py

mypy:
	uv run mypy src bot.py

up_test:
	uv run python test.py

revision: build
	- read -p "Enter revision message: " revision_message && \
	$(DOCKER_COMPOSE_RUN) alembic revision --autogenerate -m "$$revision_message"

upgrade_head: build
	- $(DOCKER_COMPOSE_RUN) alembic upgrade head