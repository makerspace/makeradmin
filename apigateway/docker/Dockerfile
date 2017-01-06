FROM hhvm/hhvm:latest

# Download and install composer
RUN    apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -r /var/lib/apt/lists/* \
    && curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Install stuff in vendor/
RUN composer update -d /var/www/html

# HHVM configuration files
ADD server.ini /etc/hhvm/server.ini
RUN touch /etc/hhvm/site.ini

EXPOSE 80

CMD ["/usr/bin/hhvm", "-m", "server", "-c", "/etc/hhvm/server.ini", "-c", "/etc/hhvm/site.ini"]
