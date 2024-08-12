FROM python:3.10-alpine3.18

WORKDIR /usr/src/app

# Install system dependencies required for Python packages
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev make curl libzbar zbar-dev openssh-client

# Install Python dependencies using pip and requirements.txt
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Compile translations
RUN pybabel compile -d bot_server/locales

# Cleanup unnecessary files and cache
RUN rm -rf /root/.cache

# Add a non-root user, change file ownership, and switch to it
RUN adduser -D appuser \
    && chown -R appuser:appuser .

USER appuser

CMD ["python", "-m", "bot"]
