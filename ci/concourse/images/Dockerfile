FROM alpine:3.13.6

COPY requirements.txt /
COPY requirements.yml /

RUN apk update && \
    apk add py3-virtualenv python3-dev gcc musl-dev libffi-dev git jq && \
    virtualenv -p python3 /venv && \
    source /venv/bin/activate && \
    pip3 install --upgrade pip && \
    pip3 install -r /requirements.txt && \
    ansible-galaxy collection install -r /requirements.yml
