FROM python:3.12-slim

WORKDIR /app

COPY docker/factoryops/requirements.txt /tmp/factoryops-requirements.txt
RUN pip install --no-cache-dir -r /tmp/factoryops-requirements.txt

COPY factoryops /app/factoryops
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

EXPOSE 8001

CMD ["python", "-m", "factoryops.bootstrap.container_start"]
