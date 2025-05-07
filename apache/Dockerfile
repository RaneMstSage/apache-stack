FROM debian:stable
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y \
    wget build-essential pkg-config autoconf libtool bison re2c cmake \
    libssl-dev libexpat1-dev libxml2-dev libjansson-dev liblua5.3-dev \
    zlib1g-dev libbrotli-dev libnghttp2-dev libpcre3-dev libldap2-dev libsasl2-dev \
    libpsl-dev perl python3 python3-dev python3-venv swig scons apache2-utils openssl ca-certificates \
    sqlite3 libsqlite3-dev libutf8proc-dev libserf-dev uuid-dev liblz4-dev \
    default-jdk libperl-dev ruby ruby-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src

# Download sources (exact 1-for-1 versions)
RUN wget https://zlib.net/zlib-1.3.1.tar.gz \
 && wget https://github.com/PCRE2Project/pcre2/releases/download/pcre2-10.45/pcre2-10.45.tar.gz \
 && wget https://github.com/libexpat/libexpat/releases/download/R_2_6_4/expat-2.6.4.tar.gz \
 && wget https://www.openssl.org/source/openssl-3.3.3.tar.gz \
 && wget https://download.gnome.org/sources/libxml2/2.13/libxml2-2.13.6.tar.xz \
 && wget https://github.com/akheron/jansson/releases/download/v2.14/jansson-2.14.tar.gz \
 && wget https://github.com/google/brotli/archive/refs/tags/v1.1.0.tar.gz -O brotli-1.1.0.tar.gz \
 && wget https://www.lua.org/ftp/lua-5.4.7.tar.gz \
 && wget https://downloads.apache.org/apr/apr-1.7.5.tar.gz \
 && wget https://downloads.apache.org/apr/apr-util-1.6.3.tar.gz \
 && wget https://github.com/nghttp2/nghttp2/releases/download/v1.64.0/nghttp2-1.64.0.tar.gz \
 && wget https://curl.se/download/curl-8.12.1.tar.gz \
 && wget https://downloads.apache.org/httpd/httpd-2.4.63.tar.gz \
 && wget https://downloads.apache.org/httpd/mod_fcgid/mod_fcgid-2.3.9.tar.gz \
 && wget https://downloads.apache.org/subversion/subversion-1.14.5.tar.gz

# Build ZLIB
RUN tar xzf zlib-1.3.1.tar.gz && cd zlib-1.3.1 \
 && ./configure && make && make install

# Build PCRE2
RUN tar xzf pcre2-10.45.tar.gz && cd pcre2-10.45 \
 && ./configure && make && make install

# Build EXPAT
RUN tar xzf expat-2.6.4.tar.gz && cd expat-2.6.4 \
 && ./configure && make && make install

# Build OPENSSL
RUN tar xzf openssl-3.3.3.tar.gz && cd openssl-3.3.3 \
 && ./config --prefix=/usr/local/ssl --openssldir=/usr/local/ssl shared zlib \
 && make && make install

# Build LIBXML2
RUN tar xf libxml2-2.13.6.tar.xz && cd libxml2-2.13.6 \
 && ./configure && make && make install

# Build JANSSON
RUN tar xzf jansson-2.14.tar.gz && cd jansson-2.14 \
 && mkdir build && cd build && cmake .. && make && make install

# Build BROTLI
RUN tar xzf brotli-1.1.0.tar.gz && cd brotli-1.1.0 \
 && mkdir build && cd build && cmake .. && make && make install

# Build LUA
RUN tar xzf lua-5.4.7.tar.gz && cd lua-5.4.7 \
 && make linux && make install

# Build APR
RUN tar xzf apr-1.7.5.tar.gz && cd apr-1.7.5 \
 && ./configure && make && make install

# Build APR-UTIL with LDAP support
RUN tar xzf apr-util-1.6.3.tar.gz && cd apr-util-1.6.3 \
 && ./configure --with-apr=/usr/local/apr --with-ldap \
 && make && make install

# Build NGHTTP2
RUN tar xzf nghttp2-1.64.0.tar.gz && cd nghttp2-1.64.0 \
 && ./configure && make && make install

# Build CURL
RUN tar xzf curl-8.12.1.tar.gz && cd curl-8.12.1 \
 && ./configure --with-ssl --with-nghttp2 --with-brotli --enable-ldap --enable-ldaps --enable-unicode \
 && make && make install

# Build and install Apache HTTPD
RUN tar xzf httpd-2.4.63.tar.gz && cd httpd-2.4.63 \
 && ./configure --enable-so --enable-ssl --enable-http2 --enable-brotli --enable-lua \
    --enable-dav --enable-dav-fs --enable-dav-lock --enable-authnz-ldap --enable-ldap \
    --enable-mods-shared=all --with-mpm=event --with-curl=/usr/local \
 && make && make install

# Build mod_fcgid, explicitly providing path to apxs
RUN tar xzf mod_fcgid-2.3.9.tar.gz \
 && cd mod_fcgid-2.3.9 \
 && APXS=/usr/local/apache2/bin/apxs ./configure.apxs \
 && make \
 && make install

# Add mod_wsgi for Python integration
RUN wget https://github.com/GrahamDumpleton/mod_wsgi/archive/refs/tags/4.9.4.tar.gz -O mod_wsgi-4.9.4.tar.gz \
 && tar xzf mod_wsgi-4.9.4.tar.gz \
 && cd mod_wsgi-4.9.4 \
 && ./configure --with-apxs=/usr/local/apache2/bin/apxs --with-python=/usr/bin/python3 \
 && make \
 && make install

 # Create Python virtual environment that Apache config expects
RUN python3 -m venv /usr/local/apache2/python-env && \
/usr/local/apache2/python-env/bin/pip install --upgrade pip wheel setuptools

# Download and install py3c (required for Python bindings)
RUN wget https://github.com/encukou/py3c/archive/refs/tags/v1.4.tar.gz -O py3c-1.4.tar.gz \
 && tar xzf py3c-1.4.tar.gz \
 && cd py3c-1.4 \
 && make install

# Build Subversion with all language bindings
RUN tar xzf subversion-1.14.5.tar.gz && cd subversion-1.14.5 \
 && ./configure --prefix=/usr/local --with-apr=/usr/local/apr --with-apr-util=/usr/local/apr \
    --with-serf --with-utf8proc \
    --enable-javahl --with-jdk=/usr/lib/jvm/default-java \
    --with-swig --with-apxs=/usr/local/apache2/bin/apxs \
    --with-apache-libexecdir=/usr/local/apache2/modules \
 && make \
 && make install \
 && make install-tools \
 && make install-javahl \
 && make swig-pl \
 && make install-swig-pl \
 && make swig-py \
 && make install-swig-py \
 && make swig-rb \
 && make install-swig-rb

# Set up dynamic linker to find libraries
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/local.conf && ldconfig

# Check if modules were installed correctly
RUN ls -la /usr/local/apache2/modules/mod_*svn* || echo "Apache SVN modules not found"

# Cleanup
RUN rm -rf /usr/src/*

EXPOSE 80 443
CMD ["/usr/local/apache2/bin/httpd", "-D", "FOREGROUND"]