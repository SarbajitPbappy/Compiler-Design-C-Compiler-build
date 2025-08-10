# syntax=docker/dockerfile:1.6
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++ make flex bison libfl-dev ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY server/ server/
COPY web/ web/
COPY tools/ tools/

# Build the Flex/Bison scanner
RUN make -C tools && mv tools/codescan /usr/local/bin/codescan

# Install Python deps
RUN pip install --no-cache-dir -r server/requirements.txt

EXPOSE 8000

# Non-root user
RUN useradd -m appuser
USER appuser

ENV PORT=8000

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
