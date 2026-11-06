FROM python:3.11-alpine3.24@sha256:bb1d70c1df30d8ee1e05214dbe82d6cdfd29833c1f47ce917f20991aca93acaa

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
