FROM node:24.14.0-alpine@sha256:7fddd9ddeae8196abf4a3ef2de34e11f7b1a722119f91f28ddf1e99dcafdf114 AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/index.html frontend/app.js frontend/styles.css frontend/vite.config.js ./
COPY frontend/config ./config
COPY frontend/public ./public
RUN npm run build

FROM nginx:1.30.6-trixie@sha256:66b50d24288dba67f3d000b31223daefc4868c58d29aaacb6a4ff9771597b5eb
ARG OCI_SOURCE=https://github.com/Code-Omega-Solutions/TextToSpeech
ARG OCI_REVISION=unknown
ARG OCI_VERSION=local

LABEL org.opencontainers.image.title="Private Speech Studio frontend" \
      org.opencontainers.image.description="Static speech frontend and Nginx proxy; third-party terms are documented in the image." \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.url="${OCI_SOURCE}" \
      org.opencontainers.image.documentation="${OCI_SOURCE}/blob/${OCI_REVISION}/THIRD_PARTY_NOTICES.md" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.version="${OCI_VERSION}" \
      org.opencontainers.image.vendor="Code-Omega-Solutions" \
      com.code-omega-solutions.license-scope="Mixed; see /usr/share/doc/*/copyright and the bundled third-party notice." \
      com.code-omega-solutions.third-party-notices="/usr/share/doc/texttospeech-frontend/THIRD_PARTY_NOTICES.md" \
      com.code-omega-solutions.source-offer="/usr/share/doc/texttospeech-frontend/SOURCE_OFFER.md" \
      com.code-omega-solutions.runtime-package-inventory="/usr/share/doc/texttospeech-frontend/RUNTIME-PACKAGES.txt"

RUN rm /etc/nginx/conf.d/default.conf /usr/share/nginx/html/index.html /usr/share/nginx/html/50x.html
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/docker/default.conf.template /etc/nginx/templates/default.conf.template
COPY --chmod=555 frontend/docker/entrypoint.sh /entrypoint.sh
COPY LICENSE NOTICE THIRD_PARTY_NOTICES.md SOURCE_OFFER.md /usr/share/doc/texttospeech-frontend/
RUN set -eu; \
    dpkg-query -W -f='${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\n' \
      | sort > /usr/share/doc/texttospeech-frontend/RUNTIME-PACKAGES.txt; \
    for package in $(dpkg-query -W | cut -f1); do \
      package=${package%%:*}; \
      test -s "/usr/share/doc/$package/copyright"; \
    done; \
    test -s /usr/share/doc/texttospeech-frontend/RUNTIME-PACKAGES.txt; \
    test -s /usr/share/doc/texttospeech-frontend/SOURCE_OFFER.md
ENV NGINX_ENVSUBST_FILTER=^TTS_UPSTREAM_URL$
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
