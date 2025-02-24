DOCKER_COMPOSE=docker compose


build:
	$(DOCKER_COMPOSE) build --parallel

up: build
	$(DOCKER_COMPOSE) up

up_local:
	poetry run python bot.py

restart_bot:
	docker-compose build bot && docker-compose restart bot

format:
	poetry run isort .
	poetry run black .

flake:
	flake8 --per-file-ignores="__init__.py:F401" --ignore E203,E501,W503 src tests bot.py

mypy:
	poetry run mypy src bot.py

up_test:

	poetry run python test.py