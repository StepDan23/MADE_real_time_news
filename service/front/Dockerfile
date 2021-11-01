FROM nginx:1.19.1-alpine

RUN mkdir /var/www
COPY ./app /var/www

# ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 80

STOPSIGNAL SIGTERM

CMD ["nginx", "-g", "daemon off;"]