FROM python:3.13-slim-bookworm

RUN useradd --system --uid 10001 --create-home --home-dir /opt/ttwo bridge
WORKDIR /opt/ttwo
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
RUN install -d -o bridge -g bridge /var/lib/ttwo-bridge
USER bridge

ENTRYPOINT ["ttwo-paper-bridge"]
