# Hermes ID — Website & Card API

The public-facing website for [hermesid.wtf](https://hermesid.wtf) and the backend API that generates AI Identification Card images on-the-fly.

## Architecture

```
site/
├── index.html          # Landing page (single-page app)
├── card_api.py          # Flask API — generates card PNGs + Twitter Card pages
├── favicon.png          # Site favicon
├── requirements.txt     # Python dependencies
└── cards/               # Pre-generated example cards
    ├── teknium.png
    ├── karpathy.png
    ├── sama.png
    ├── elonmusk.png
    └── emaboringkass.png
```

## Features

- **Landing page** — Cyberpunk-themed single-page site with scroll-based card gallery, 3D card flip animations, ASCII rain background, and glowing card aura
- **"Get Your Card" modal** — Enter any X handle → generates a card via the API → share on X or download as PNG
- **Card API** (`/api/card?handle=xxx`) — Generates a pixel-perfect AI ID Card PNG with:
  - Real X profile picture (fetched via [unavatar.io](https://unavatar.io), free, no API key)
  - Manga-style halftone avatar filter
  - 8-axis radar chart
  - Progress bars for all dimensions
  - Unique barcode per handle
- **Twitter Card pages** (`/card/<handle>`) — HTML pages with Open Graph / Twitter Card meta tags so card images appear as rich previews when shared on X

## Quick Start (Local Development)

```bash
cd site/

# Install dependencies
pip install -r requirements.txt

# Run the API server
python card_api.py
# → http://127.0.0.1:5050

# Test it
curl http://127.0.0.1:5050/api/card?handle=teknium -o test.png
curl http://127.0.0.1:5050/api/health
```

Serve `index.html` separately (e.g. `python -m http.server 8080`) or configure nginx to serve static files.

## Production Deployment (VPS)

### 1. Server Setup

```bash
ssh root@your-server

apt update && apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

# Create app directory
mkdir -p /var/www/hermesid.wtf
```

### 2. Upload Files

```bash
# From your local machine
scp -r site/* root@your-server:/var/www/hermesid.wtf/
```

### 3. Python Environment

```bash
cd /var/www/hermesid.wtf
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Systemd Service

Create `/etc/systemd/system/hermes-card-api.service`:

```ini
[Unit]
Description=Hermes ID Card API
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/hermesid.wtf
ExecStart=/var/www/hermesid.wtf/venv/bin/gunicorn card_api:app -b 127.0.0.1:5050 -w 2 --timeout 60
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now hermes-card-api
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/hermesid.wtf`:

```nginx
server {
    listen 80;
    server_name hermesid.wtf www.hermesid.wtf;

    root /var/www/hermesid.wtf;
    index index.html;

    # Static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Card API (proxied to Flask)
    location /api/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }

    # Twitter Card pages
    location /card/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -sf /etc/nginx/sites-available/hermesid.wtf /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 6. SSL (Let's Encrypt)

```bash
certbot --nginx -d hermesid.wtf -d www.hermesid.wtf
```

### 7. DNS

Point your domain to your server:

| Type | Name | Value |
|------|------|-------|
| A | @ | your.server.ip |
| CNAME | www | hermesid.wtf |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/card?handle=xxx` | GET | Generate and return a PNG card image |
| `/api/health` | GET | Health check (`{"status": "ok"}`) |
| `/card/<handle>` | GET | HTML page with Twitter Card meta tags for rich link previews |

## How Card Scores Work

For the website demo, scores are deterministically generated per handle (same handle always gets the same scores). This ensures consistency without requiring LLM calls.

For **real LLM-based scoring**, use the Hermes ID skill with Hermes Agent — see [`skills/social-media/hermes-id/`](../skills/social-media/hermes-id/).
