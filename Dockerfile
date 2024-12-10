FROM python:3.9-buster

ENV HF_HOME=/opt/app/huggingface

# Install nginx and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx vim libxml2-dev libxmlsec1-dev clamav-daemon clamav-freshclam clamav-unofficial-sigs \
    && rm -rf /var/lib/apt/lists/*

COPY nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# Create directories
RUN mkdir -p $HF_HOME && chown -R www-data:www-data $HF_HOME
RUN mkdir -p /opt/app/pip_cache
RUN mkdir -p /opt/app/openlxp-xss
RUN mkdir -p /opt/app/huggingface

# Copy requirements and install dependencies
COPY requirements.txt start-server.sh start-app.sh /opt/app/
RUN chmod +x /opt/app/start-server.sh /opt/app/start-app.sh

# Install Python dependencies
WORKDIR /opt/app
RUN pip install -r requirements.txt --cache-dir /opt/app/pip_cache

# Pre-download the SentenceTransformer model now that it's installed
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY ./app /opt/app/openlxp-xss/

RUN chown -R www-data:www-data /opt/app

WORKDIR /opt/app/openlxp-xss/
RUN freshclam
RUN service clamav-daemon start

EXPOSE 8020
STOPSIGNAL SIGTERM
