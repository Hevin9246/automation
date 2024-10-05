ARG PYTHON_VERSION=3.12.0
FROM python:${PYTHON_VERSION}-slim as base


# install chromedriver
RUN apt-get update && apt-get install -y \
chromium chromium-driver

# upgrade pip
RUN pip install --upgrade pip

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.

RUN df -h
RUN du -sh /app || true

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

RUN df -h
RUN du -sh /app || true

# Switch back to root to create and set permissions for the 'uploads' directory
USER root
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

RUN df -h
RUN du -sh /app/uploads || true

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
CMD gunicorn 'app:app' --bind=0.0.0.0:8000 --timeout 120  # Set timeout to 120 seconds
