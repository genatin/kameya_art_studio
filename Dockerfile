FROM python:3.13-slim

ARG POETRY_HOME=/etc/poetry
ENV UV_HTTP_TIMEOUT=120
ENV UV_CACHE_DIR=/root/.cache/uv

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get -y install --no-install-recommends curl tini && \
    pip install uv==0.5.9 && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="${PATH}:${POETRY_HOME}/bin"

COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    (uv sync --locked --no-editable || \
     echo "Retrying..." && sleep 30 && uv sync --locked --no-editable)

COPY bot.py alembic.ini ./
COPY ./src ./src
COPY ./static_data ./static_data
COPY ./alembic ./alembic


ENTRYPOINT ["tini", "--"]
CMD ["/bin/bash", "-c", "uv run alembic upgrade head && uv run ./bot.py"]
