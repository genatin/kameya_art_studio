FROM python:3.13-slim

ARG POETRY_HOME=/etc/poetry

RUN apt-get update && \
    export DEBIAN_FRONTEND=noninteractive && \ 
    apt-get -y install --no-install-recommends curl tini && \
    pip install uv==0.5.9 && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*


ENV PATH="${PATH}:${POETRY_HOME}/bin"

COPY uv.lock pyproject.toml ./

RUN uv sync \
    --locked \
    --no-editable

COPY ./src ./src
COPY ./bot.py ./bot.py
COPY ./static_data ./static_data


ENTRYPOINT ["tini", "--" ]

CMD ["uv", "run", "./bot.py"]
