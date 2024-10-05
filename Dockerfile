FROM python:3.9-alpine

# Install necessary build dependencies for Python packages and SSL
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    linux-headers \
    bash

# Set up virtual environment for the proxy
RUN python3.9 -m venv /proxy/venv
ENV PATH="/proxy/venv/"

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN pip install -U ua_generator requests

WORKDIR /proxy

COPY . .

EXPOSE 8080

CMD ["python", "proxy.py"]


