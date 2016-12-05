FROM php:7.0.12-fpm

# Install nginx
RUN apt-get update && apt-get install -y --no-install-recommends nginx && rm -r /var/lib/apt/lists/*

# Set up nginx default host configuration
RUN rm /etc/nginx/sites-available/default
COPY conf/nginx_default_host /etc/nginx/sites-available/default

# Set up php-fpm config
RUN rm /usr/local/etc/php-fpm.conf
COPY conf/php-fpm.conf /usr/local/etc/php-fpm.conf
COPY conf/php-fpm-www.conf /etc/php-fpm.d/www.conf

# Install PDO
RUN docker-php-ext-configure pdo_mysql && \
    docker-php-ext-install pdo_mysql

# Forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80

COPY myStartupScript.sh /usr/local/myscripts/myStartupScript.sh
CMD ["/usr/local/myscripts/myStartupScript.sh"]