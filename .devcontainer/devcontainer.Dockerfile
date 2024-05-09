# syntax=docker/dockerfile:1.4
FROM mcr.microsoft.com/devcontainers/base:1.2.1-ubuntu22.04
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update
RUN apt-get install --no-install-recommends --no-install-suggests -yqq \
    ca-certificates \
    python3.11-dev \
    python3.11-doc \
    python3.11-venv \
    python3-pip
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN curl -fsSL https://github.com/wagoodman/dive/releases/download/v0.12.0/dive_0.12.0_linux_amd64.tar.gz | tar -xz dive -C /usr/local/bin/

USER vscode

# create a $BASH_ENV-file for common bash configurations
WORKDIR /devcontainersetup/
ENV BASH_ENV /home/vscode/.env
RUN touch "$BASH_ENV" && \
    echo '. "'"$BASH_ENV"'"' >> ~/.bashrc && \
    echo '. "'"$BASH_ENV"'"' >> ~/.zshrc

# install node via nvm
RUN curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | PROFILE="$BASH_ENV" bash
COPY .nvmrc ./
RUN nvm install

# setup python virtual environment and install python dependencies
COPY requirements.txt ./
COPY api/requirements.txt api/
RUN python3 -m venv .venv
RUN echo '. /devcontainersetup/.venv/bin/activate' >> "$BASH_ENV"
RUN python3 -m pip install --upgrade -r requirements.txt
