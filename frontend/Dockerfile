FROM nginx:alpine

RUN apk add --update nodejs-npm && rm -rf /var/cache/apk/*

RUN mkdir -p /data/src && mkdir -p /data/dist/js
COPY ./src/ /data/src
COPY ./webpack.config.js ./package.json /data/

# Configuration file for nginx
COPY ./docker/nginx_default_host /etc/nginx/conf.d/default.conf

# Add files to web root
RUN mkdir -p /var/www/html
COPY ./dist/ /var/www/html

RUN cd /data && \
    npm install && \
    node /data/node_modules/webpack/bin/webpack.js --config /data/webpack.config.js && \
    mv -f /data/dist/js/app.js /var/www/html/js/ && \
    rm -rf /data

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
