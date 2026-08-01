# WES OS — Company Engine backend image
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# git is required by the Autonomous Development Engine (real git sandbox +
# branch + commit). Sprint 24 activation fix. [P0-2]
RUN apt-get update \
    && apt-get install -y --no-install-recommends git openssh-client \
    && rm -rf /var/lib/apt/lists/*

# System deps for psycopg2 runtime are included in slim; build tools not needed
# because psycopg2-binary ships wheels.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# entrypoint runs migrations (+ optional seed) then starts the API server.
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
