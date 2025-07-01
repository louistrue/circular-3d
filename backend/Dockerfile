FROM python:3.9-slim

# Install system dependencies including Docker CLI and Intel MKL
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add Intel MKL repository and install MKL libraries
RUN wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | apt-key add - && \
    echo "deb https://apt.repos.intel.com/mkl all main" > /etc/apt/sources.list.d/intel-mkl.list && \
    apt-get update && \
    apt-get install -y intel-mkl-2020.0-088 && \
    rm -rf /var/lib/apt/lists/*

# Set MKL environment variables
ENV LD_LIBRARY_PATH=/opt/intel/mkl/lib/intel64:$LD_LIBRARY_PATH
ENV MKL_NUM_THREADS=1

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