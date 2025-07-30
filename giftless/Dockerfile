FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Clone and install latest Giftless from GitHub with all dependencies
RUN git clone https://github.com/datopian/giftless.git /tmp/giftless && \
    cd /tmp/giftless && \
    pip install --no-cache-dir . && \
    rm -rf /tmp/giftless

# Install uWSGI
RUN pip install --no-cache-dir uwsgi

EXPOSE 5000

# Set environment
ENV GIFTLESS_CONFIG_FILE=/etc/giftless.yaml

# Run with uWSGI
CMD ["uwsgi", "-M", "-T", "--threads", "2", "-p", "2", "--manage-script-name", "--callable", "app", "--http", "0.0.0.0:5000", "--module", "giftless.app:init_app()"]