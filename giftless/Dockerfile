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

# Copy your custom authenticator
COPY apache_proxy.py /app/giftless/auth/apache_proxy.py

# Copy the config
COPY config.yaml /etc/giftless.yaml

EXPOSE 5000

# Set environment variable for config
ENV GIFTLESS_CONFIG_FILE=/etc/giftless.yaml

# Run with uWSGI
CMD ["uwsgi", "-M", "-T", "--threads", "2", "-p", "2", "--manage-script-name", "--callable", "app", "--http", "0.0.0.0:5000", "--module", "giftless.wsgi:app"]