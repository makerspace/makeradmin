FROM php:7.1.3-cli

# Install PDO
RUN docker-php-ext-configure pdo_mysql && \
    docker-php-ext-install pdo_mysql

COPY ./docker/myStartupScript.sh /usr/local/myscripts/myStartupScript.sh
CMD ["/usr/local/myscripts/myStartupScript.sh"]