FROM python:3.11-alpine@sha256:5d769f990397afbb2aca24b0655e404c0f2806d268f454b052e81e39d87abf42

RUN apk update \
    && apk add \
       bash \
       netcat-openbsd \
       less \
       curl \
       zlib-dev \
       jpeg-dev \
       build-base \
       python3-dev \
       libffi-dev \
       libressl-dev \
       linux-headers \
       inotify-tools \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /work/ && mkdir -p /work/logs

VOLUME /work/logs

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY api/default-product-image.png /work

COPY pyproject.toml uv.lock /work/
COPY config /config
COPY scripts/build_locales.py /scripts/

WORKDIR /work
RUN uv sync --no-dev --frozen

# Activate the virtual environment for subsequent commands
ENV PATH="/work/.venv/bin:$PATH"

COPY api/run.sh api/dispatch_messages.sh api/accessy_syncer.sh /work/

COPY api/src /work/src

RUN python3 /scripts/build_locales.py --locale-path=/config/locales/ --locale-override-path=/config/locale_overrides --output-py=/work/src/i18n --default-locale=en --modules admin common

EXPOSE 80

WORKDIR "/work/src"

CMD ["/work/run.sh"]
