FROM python:3.13-slim

ARG POETRY_HOME=/etc/poetry

RUN apt-get update && apt-get install -y --no-install-recommends curl tini && \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=${POETRY_HOME} python - --version 1.8.4 && \
    apt-get remove -y --purge build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="${PATH}:${POETRY_HOME}/bin"

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-cache --without dev && \
    rm -rf ~/.cache ~/.config/pypoetry/auth.toml


COPY init_db.py service_account.json ./

COPY ./src ./src
COPY ./bot.py ./bot.py

ENTRYPOINT ["tini", "--" ]

CMD ["/bin/bash", "-c", "python ./init_db.py && python ./bot.py"]
