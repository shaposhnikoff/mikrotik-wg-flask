# MikroTik WireGuard Config Generator

A Flask + HTMX web app that generates WireGuard server and client configurations for MikroTik RouterOS.

This is a Python rewrite of the [original client-side Vue.js app](https://github.com/shaposhnikoff/mikrotik-wireguard-config-generator), with server-side key generation and persistent config storage.

## Features

- Generates X25519 keypairs and preshared keys server-side (Python `cryptography` lib)
- Produces paste-ready MikroTik RouterOS CLI commands
- Produces standard WireGuard `.conf` files for clients
- QR codes generated server-side — scan directly with the WireGuard mobile app
- Download all client configs as a ZIP
- Persists server and client configs in SQLite
- No JavaScript required (HTMX + Jinja2)

## Screenshot

```
┌─────────────────────────────┬──────────────────────────────┐
│  Server Parameters (form)   │  Client Configs              │
│                             │  ┌──────────────────────┐   │
│  [Generate Server Config]   │  │ ▓▓▓▓ QR ▓▓▓▓  conf  │   │
│                             │  │ Client_2  172.22.0.2 │   │
│  RouterOS Commands          │  └──────────────────────┘   │
│  /interface wireguard ...   │  ┌──────────────────────┐   │
│                             │  │ ▓▓▓▓ QR ▓▓▓▓  conf  │   │
│  [Generate 3 Clients]       │  │ Client_3  172.22.0.3 │   │
│                             │  └──────────────────────┘   │
└─────────────────────────────┴──────────────────────────────┘
```

## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Setup

```bash
git clone https://github.com/shaposhnikoff/mikrotik-wg-flask
cd mikrotik-wg-flask

uv venv
uv pip install -r requirements.txt

python run.py
# → http://localhost:5000
```

## Usage

1. Fill in the server parameters (endpoint, port, network, etc.)
2. Click **Generate Server Config** — RouterOS commands appear on the left
3. Click **Generate Clients** — client cards with QR codes appear on the right
4. Paste RouterOS commands into your MikroTik terminal
5. Scan QR codes with the WireGuard mobile app, or download the ZIP

## Project Structure

```
app/
├── __init__.py              # Flask app factory
├── models.py                # ServerConfig, ClientConfig (SQLAlchemy)
├── routes/
│   ├── main.py              # Page routes: /, /configs, /configs/<id>
│   └── api.py               # /api/* endpoints
├── services/
│   ├── keygen.py            # X25519 keypair + preshared key generation
│   ├── config_builder.py    # RouterOS + WireGuard .conf builders
│   └── qr.py                # QR code PNG generation
└── templates/               # Jinja2 + HTMX (Bulma CSS)
config.py
run.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Main generator page |
| `POST` | `/api/generate-server` | Generate server keypair, save to DB |
| `POST` | `/api/generate-clients` | Generate client configs for a server |
| `GET` | `/api/qr/<client_id>` | Inline QR PNG |
| `GET` | `/api/download/clients/<server_id>` | ZIP of all client `.conf` files |
| `GET` | `/api/download/qr/<client_id>` | Download single QR PNG |
| `GET` | `/configs` | List saved server configs |
| `GET` | `/configs/<server_id>` | View a saved config |

## License

GPL-2.0
