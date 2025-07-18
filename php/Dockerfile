FROM php:8.3-fpm

# Install dependencies needed for building PHP extensions
# Note: libldap2-dev is required for LDAP support
RUN apt-get update && apt-get install -y \
        libfreetype6-dev \
        libjpeg62-turbo-dev \
        libpng-dev \
        libzip-dev \
        libxml2-dev \
        libonig-dev \
        libldap2-dev \
        libssl-dev \
        libsasl2-dev \
        vim \
        neovim \
    && docker-php-ext-install -j$(nproc) \
        gd \
        mysqli \
        pdo_mysql \
        zip \
        opcache \
        mbstring \
        xml \
        ldap \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure LDAP extension to support different protocol versions
RUN { \
        echo 'ldap.max_links = -1'; \
    } > /usr/local/etc/php/conf.d/ldap.ini

# Set recommended PHP.ini settings for OPcache
RUN { \
        echo 'opcache.memory_consumption=128'; \
        echo 'opcache.interned_strings_buffer=8'; \
        echo 'opcache.max_accelerated_files=4000'; \
        echo 'opcache.revalidate_freq=2'; \
        echo 'opcache.fast_shutdown=1'; \
        echo 'opcache.enable_cli=1'; \
    } > /usr/local/etc/php/conf.d/opcache-recommended.ini

# Additional security-focused PHP settings
RUN { \
        echo 'expose_php = Off'; \
        echo 'display_errors = Off'; \
        echo 'display_startup_errors = Off'; \
        echo 'log_errors = On'; \
        echo 'error_log = /var/log/php/error.log'; \
        echo 'post_max_size = 10M'; \
        echo 'upload_max_filesize = 10M'; \
        echo 'max_execution_time = 30'; \
        echo 'max_input_time = 30'; \
        echo 'memory_limit = 128M'; \
    } > /usr/local/etc/php/conf.d/security.ini

# Create a non-root user for running PHP-FPM
RUN groupadd -g 1000 www-data 2>/dev/null || true && \
    useradd -u 1000 -g www-data -s /bin/false -d /var/www -M www-data 2>/dev/null || true

# Create necessary directories with proper permissions
RUN mkdir -p /var/log/php /var/www/html && \
    chown -R www-data:www-data /var/log/php /var/www/html

# Switch to non-root user
USER www-data

WORKDIR /var/www/html

# Expose only the PHP-FPM port
EXPOSE 9000

# Health check to ensure PHP-FPM is responding
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1