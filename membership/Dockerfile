FROM hhvm/hhvm:latest

# Download and install composer
RUN    apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -r /var/lib/apt/lists/* \
    && curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Add all the lumen files
ADD ./lumen /var/www/html/
RUN composer install -d /var/www/html

# HHVM configuration files
ADD ./docker/server.ini /etc/hhvm/server.ini
RUN touch /etc/hhvm/site.ini

EXPOSE 80

COPY ./docker/myStartupScript.sh /usr/local/myscripts/myStartupScript.sh
CMD ["/usr/local/myscripts/myStartupScript.sh"]