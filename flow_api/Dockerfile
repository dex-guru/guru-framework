FROM python:3.10-alpine3.18

# Set environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_HOME="/etc/poetry" \
    POETRY_VERSION=1.7.0 \
    PATH="/etc/poetry/bin:$PATH"

WORKDIR /usr/src/app

COPY . .

# Install system dependencies required for Python packages
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev make curl libzbar zbar-dev openssh-client


# Install Poetry using the official installer script and ensure poetry command is available
RUN curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies with Poetry
RUN poetry install --without dev --no-root

# Compile translations
RUN pybabel compile -d bot/locales

# Cleanup unnecessary files and cache
RUN rm -rf /root/.cache && rm -rf $POETRY_CACHE_DIR

# Add a non-root user, change file ownership, and switch to it
RUN adduser -D appuser \
    && chown -R appuser:appuser .

USER appuser

CMD ["python", "-m", "bot"]
