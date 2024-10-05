FROM python:3.9-alpine

# Install necessary build dependencies for Python packages and SSL
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    linux-headers \
    bash \
    py3-pip

# Set up virtual environment for the proxy
RUN python3 -m venv /proxy/venv
# activate virtual environment
ENV VIRTUAL_ENV=/proxy/venv
ENV PATH="proxy/venv/bin:$PATH"

# Install dependencies 
COPY requirements.txt .
RUN pip3 install -r requirements.txt


WORKDIR /proxy

COPY . .

EXPOSE 8080

CMD ["python3.9", "proxy.py"]


