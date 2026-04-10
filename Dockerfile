# ── Stage 1: build ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir hatchling \
 && pip install --no-cache-dir .

# ── Stage 2: runtime ──────────────────────────────────────────
FROM python:3.11-slim

RUN groupadd --gid 1000 app \
 && useradd  --uid 1000 --gid app --shell /bin/bash app

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages \
                    /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/hermes-dashboard \
                    /usr/local/bin/hermes-dashboard

ENV HERMES_HOME=/data/.hermes
RUN mkdir -p /data/.hermes && chown -R app:app /data/.hermes

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8090/api/docs')" || exit 1

USER app

ENTRYPOINT ["hermes-dashboard"]
CMD []
