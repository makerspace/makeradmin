FROM nginx:alpine

RUN apk add --update nodejs-npm && rm -rf /var/cache/apk/*

RUN mkdir -p /data/src && mkdir -p /data/dist/js

# Copy package file first, to avoid having to install dependencies every time a source file is updated
COPY ./webpack.config.js ./package.json /data/
WORKDIR /data
RUN npm install

COPY ./src/ /data/src

# Configuration file for nginx
COPY ./docker/nginx_default_host /etc/nginx/conf.d/default.conf

# Add files to web root
RUN mkdir -p /var/www/html
COPY ./dist/ /var/www/html

RUN node /data/node_modules/webpack/bin/webpack.js --config /data/webpack.config.js --progress

WORKDIR /

RUN mv -f /data/dist/js/app.js /var/www/html/js/ && rm -rf /data

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
