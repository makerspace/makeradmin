FROM python:3.11-alpine@sha256:5d769f990397afbb2aca24b0655e404c0f2806d268f454b052e81e39d87abf42

RUN mkdir /work

COPY requirements.txt /work

RUN pip install -U pip \
    && pip install -r /work/requirements.txt

WORKDIR "/work/"

ENTRYPOINT ["python3", "-m", "mkdocs"]
