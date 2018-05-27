FROM hhvm/hhvm:3.21.10

# Download and install composer
# Note: netcat is required by the wait-for script
RUN    apt-get update \
    && apt-get install -y --no-install-recommends curl netcat \
    && rm -r /var/lib/apt/lists/* \
    && curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Add and install common dependencies
ADD ./lumen/composer.json /var/www/html/
ADD ./lumen/composer.lock /var/www/html/

RUN composer update makeradmin/makeradmin-library --no-scripts --no-autoloader --no-suggest -d /var/www/html

ADD ./docker/wait-for /usr/local/myscripts/
