FROM python:latest

RUN apt update && \
    apt install -y git \
    python3-pip \
    vim && \
    rm -rf /var/lib/apt/*

RUN pip3 install --upgrade pip

RUN pip3 install --no-cache pandas seaborn matplotlib numpy pyyaml requests pytz discord