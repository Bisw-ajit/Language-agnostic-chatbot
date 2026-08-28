FROM python:3.11-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./backend
RUN mkdir -p backend/chroma_data backend/uploads
ENV PYTHONPATH=/workspace
WORKDIR /workspace/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
