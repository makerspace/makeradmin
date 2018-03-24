FROM hhvm/hhvm:latest

# Download and install composer
RUN    apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -r /var/lib/apt/lists/* \
    && curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Add and install dependencies
# This is done in a different step from adding the source code to allow docker to cache the results
# and thus improve build times significantly if no dependencies have changed.
ADD ./lumen/composer.json /var/www/html/
ADD ./lumen/composer.lock /var/www/html/
RUN composer install --no-scripts --no-autoloader -d /var/www/html

# Add all the other lumen files
ADD ./lumen /var/www/html/

# Run the remaining composer scripts (with hhvm's jit disabled to reduce startup time)
RUN hhvm -d hhvm.jit=0 /usr/local/bin/composer dump-autoload -d /var/www/html

# HHVM configuration files
ADD ./docker/server.ini /etc/hhvm/server.ini
RUN touch /etc/hhvm/site.ini

EXPOSE 80

COPY ./docker/myStartupScript.sh /usr/local/myscripts/myStartupScript.sh
CMD ["/usr/local/myscripts/myStartupScript.sh"]