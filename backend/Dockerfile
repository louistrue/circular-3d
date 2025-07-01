FROM python:3.9-slim

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh --dry-run && \
    rm get-docker.sh && \
    curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz | tar xzvf - --strip 1 -C /usr/local/bin docker/docker

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads processing

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 