FROM node:19-alpine

RUN apk add --no-cache tzdata
ENV TZ Europe/Stockholm

RUN mkdir -p /work/src && mkdir -p /work/dist/js

# Copy package file first, to avoid having to install dependencies every time a source file is updated
COPY ./webpack.config.js ./tsconfig.json ./package.json ./package-lock.json /work/

WORKDIR /work

RUN npm install

COPY ./src/ /work/src
COPY ./jestSetup.js /work/

RUN npm run eslint

RUN npm run test

RUN npm run build
RUN echo tsc --version

FROM nginx:alpine

# Configuration file for nginx
COPY ./docker/nginx_default_host /etc/nginx/conf.d/default.conf

# Add files to web root
RUN mkdir -p /var/www/html
COPY ./dist/ /var/www/html
COPY --from=0 /work/dist/ /var/www/html

EXPOSE 80

COPY ./docker/docker_entrypoint.sh /usr/local/myscripts/docker_entrypoint.sh
CMD ["/usr/local/myscripts/docker_entrypoint.sh"]
