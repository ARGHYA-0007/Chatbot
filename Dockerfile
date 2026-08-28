# Base image: lightweight Python 3.11 (slim = fewer OS packages, smaller image)
FROM python:3.11-slim

# All following commands run from /app inside the container
WORKDIR /app

# Install system-level build tools (gcc) needed to compile some Python packages
# (langchain/pydantic dependencies sometimes need this during pip install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first (before the rest of the code)
# so Docker can cache this layer and skip re-installing packages
# every time you change your app code
COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

# Now copy the rest of the project (app.py, model/, etc.) into the container
COPY . .

# Document that the app listens on port 8000 (informational; doesn't publish it)
EXPOSE 8000

# Tell langchain-ollama where to find the Ollama server.
# Default assumes Ollama is running on your HOST machine, not inside this container.
# Override with `-e OLLAMA_HOST=...` at runtime if Ollama lives elsewhere (e.g. a sidecar container)
ENV OLLAMA_HOST=http://host.docker.internal:11434

# Start the FastAPI app with uvicorn
# --host 0.0.0.0 makes it reachable from outside the container (not just localhost)
# --port 8000 matches the EXPOSE above
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]