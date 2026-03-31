FROM python:3.12-slim
RUN apt-get update && apt-get install -y arp-scan curl ca-certificates && \
    curl -fsSL https://pkgs.tailscale.com/stable/debian/$(. /etc/os-release; echo $VERSION_CODENAME).noarmor.gpg | tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null && \
    curl -fsSL https://pkgs.tailscale.com/stable/debian/$(. /etc/os-release; echo $VERSION_CODENAME).tailscale-keyring.list | tee /etc/apt/sources.list.d/tailscale.list && \
    apt-get update && apt-get install -y tailscale && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
