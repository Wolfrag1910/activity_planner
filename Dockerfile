# The Cumetria website image. python:3.12-slim is published for both
# linux/amd64 (most PCs) and linux/arm64 (the Oracle server), so the same file
# builds on either.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATA_DIR=/data

# gettext compiles the Romanian translations during the build.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Safety net for Windows clones: strip Windows line endings from the start-up
# script and make sure it's executable, so the container starts either way.
RUN sed -i 's/\r$//' docker/entrypoint.sh && chmod +x docker/entrypoint.sh

# Prepare static files and translations once, at build time.
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && DJANGO_SECRET_KEY=build-only python manage.py compilemessages --ignore=.venv

# Run as an ordinary user, not root. /data holds the database and uploads.
RUN useradd --create-home --uid 1000 cumetria \
    && mkdir -p /data \
    && chown cumetria:cumetria /data
USER cumetria

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "cumetria.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "--access-logfile", "-"]
