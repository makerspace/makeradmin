FROM nginx:alpine

# Configuration file for nginx
COPY ./docker/nginx_default_host /etc/nginx/conf.d/default.conf

# Add files to web root
COPY ./dist/ /var/www/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]