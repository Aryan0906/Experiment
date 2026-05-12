FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2 and opencv
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
