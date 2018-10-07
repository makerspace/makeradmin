FROM node:8-alpine

RUN apk add --no-cache tzdata
ENV TZ Europe/Stockholm

RUN mkdir -p /data/src && mkdir -p /data/dist/js

# Copy package file first, to avoid having to install dependencies every time a source file is updated
COPY ./webpack.config.js ./member.webpack.config.js ./package.json ./package-lock.json /data/

WORKDIR /data

RUN npm install

COPY ./src/ /data/src
COPY ./jestSetup.js /data/

RUN npm run eslint

RUN npm run test

RUN /data/node_modules/.bin/webpack --config /data/webpack.config.js
RUN /data/node_modules/.bin/webpack --config /data/member.webpack.config.js

FROM nginx:alpine

# Configuration file for nginx
COPY ./docker/nginx_default_host /etc/nginx/conf.d/default.conf

# Add files to web root
RUN mkdir -p /var/www/html
COPY ./dist/ /var/www/html
COPY --from=0 /data/dist/ /var/www/html


EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
