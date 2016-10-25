FROM nginx:alpine

COPY nginx_default_host /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
