up_local:
	poetry run python bot.py

up:
	docker build -t bot_kameya . && docker run -it bot_kameya

format:
	poetry run isort .
	poetry run black .