FROM python:3.12-slim

WORKDIR /app

# Install system deps for tcod (may need build tools depending on wheel availability)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libtcod-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip && python3 -m pip install -r /app/requirements.txt

COPY . /app

ENV LOCAL_LLM_ENDPOINT=http://ollama:11434/api/generate

CMD ["python3", "main.py"]
