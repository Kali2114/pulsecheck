FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt /tmp/requirements.txt

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt --no-cache-dir && \
    rm -f /tmp/requirements.txt

COPY app/ /app/app
COPY alembic/ /app/alembic
COPY alembic.ini /app/alembic.ini

RUN useradd -r -s /usr/sbin/nologin pulsecheck

USER pulsecheck

ENV PYTHONUNBUFFERED=1
ENV PATH="/py/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
