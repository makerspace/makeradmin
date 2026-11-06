FROM python:3.11-alpine3.24@sha256:bb1d70c1df30d8ee1e05214dbe82d6cdfd29833c1f47ce917f20991aca93acaa

RUN mkdir /work

COPY requirements.txt /work

RUN pip install -U pip \
    && pip install -r /work/requirements.txt

WORKDIR "/work/"

ENTRYPOINT ["python3", "-m", "mkdocs"]
