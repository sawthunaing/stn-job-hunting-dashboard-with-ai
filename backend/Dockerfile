FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl xz-utils \
    && rm -rf /var/lib/apt/lists/*

ARG TYPST_VERSION=v0.15.1
RUN set -eux; \
    case "$(uname -m)" in \
      x86_64)  typst_target=x86_64-unknown-linux-musl ;; \
      aarch64) typst_target=aarch64-unknown-linux-musl ;; \
      *) echo "unsupported architecture for typst: $(uname -m)" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/typst.tar.xz \
      "https://github.com/typst/typst/releases/download/${TYPST_VERSION}/typst-${typst_target}.tar.xz"; \
    tar -xJf /tmp/typst.tar.xz -C /tmp; \
    mv "/tmp/typst-${typst_target}/typst" /usr/local/bin/typst; \
    chmod +x /usr/local/bin/typst; \
    rm -rf /tmp/typst*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
