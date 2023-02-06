FROM python:latest

RUN apt update && \
    apt install -y git \
    python3-pip \
    vim && \
    rm -rf /var/lib/apt/*

RUN pip3 install --upgrade pip

RUN pip3 install --no-cache pandas seaborn matplotlib numpy pyyaml requests pytz discord yfinance requests_cache requests_ratelimiter black autoflake flake8

# For Python packages installed with user privileges
RUN echo export PATH="$HOME/.local/bin:$PATH" >> /etc/bash.bashrc