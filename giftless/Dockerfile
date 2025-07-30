FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and install latest Giftless from GitHub
RUN git clone https://github.com/datopian/giftless.git /tmp/giftless && \
    cd /tmp/giftless && \
    pip install --no-cache-dir -e . && \
    cp -r /tmp/giftless/giftless /app/ && \
    rm -rf /tmp/giftless

EXPOSE 5000

# Run with uWSGI
CMD ["uwsgi", "-M", "-T", "--threads", "2", "-p", "2", "--manage-script-name", "--callable", "app", "--http", "0.0.0.0:5000", "--module", "giftless.wsgi:app"]