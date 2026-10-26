FROM node:24.14.0-alpine AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY index.html app.js styles.css vite.config.js ./
COPY config ./config
COPY public ./public
RUN npm run build

FROM nginx:1.30.6-alpine
RUN rm /etc/nginx/conf.d/default.conf /usr/share/nginx/html/index.html /usr/share/nginx/html/50x.html
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/default.conf.template /etc/nginx/templates/default.conf.template
COPY --chmod=555 docker/entrypoint.sh /entrypoint.sh
ENV NGINX_ENVSUBST_FILTER=^TTS_UPSTREAM_URL$
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
