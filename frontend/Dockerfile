FROM makeradmin/frontend-base:1.0

FROM nginx:alpine

# Configuration file for nginx
COPY ./docker/nginx_default_host /etc/nginx/conf.d/default.conf

# Add files to web root
RUN mkdir -p /var/www/html
COPY ./dist/ /var/www/html
COPY --from=0 /data/dist/ /var/www/html


EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
