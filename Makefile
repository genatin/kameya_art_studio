up_local:
	poetry run python bot.py

up:
	docker build -t bot_kameya . && docker run -it bot_kameya

format:
	poetry run isort .
	poetry run black .

flake:
	flake8 --per-file-ignores="__init__.py:F401" --ignore E203,E501,W503 src tests main.py

mypy:
	poetry run mypy src bot.py