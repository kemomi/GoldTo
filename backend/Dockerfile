<<<<<<< HEAD
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" openai python-multipart \
    python-dotenv pydantic pydantic-settings sse-starlette networkx pypdf httpx aiofiles

# Copy source
COPY . .

# Create uploads dir
RUN mkdir -p uploads

EXPOSE 5001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
=======
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv --no-cache-dir

# Copy project files
COPY pyproject.toml .
COPY . .

# Install dependencies
RUN uv sync

EXPOSE 5001

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
>>>>>>> kemomi/main
