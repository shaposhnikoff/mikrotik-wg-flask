import io
import zipfile

from flask import Blueprint, Response, make_response, render_template, request

from app import db
from app.models import ClientConfig, ServerConfig
from app.services.config_builder import build_client_config, build_server_config
from app.services.keygen import generate_keypair, generate_preshared_key
from app.services.qr import generate_qr_png

api_bp = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------


def _parse_int(value, name, min_val, max_val):
    """Return int or raise ValueError with a user-friendly message."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an integer.")
    if not (min_val <= v <= max_val):
        raise ValueError(f"{name} must be between {min_val} and {max_val}.")
    return v


def _error_partial(message: str) -> str:
    return render_template("partials/error.html", message=message)


# ---------------------------------------------------------------------------
# POST /api/generate-server
# ---------------------------------------------------------------------------


@api_bp.route("/generate-server", methods=["POST"])
def generate_server():
    try:
        endpoint = request.form.get("endpoint", "").strip()
        if not endpoint:
            raise ValueError("Server endpoint is required.")

        port = _parse_int(request.form.get("port", ""), "Port", 1, 65535)
        interface_name = request.form.get("interface_name", "wg0").strip() or "wg0"

        network = request.form.get("network", "").strip()
        if not network or network.count(".") != 2:
            raise ValueError("Network must be a 3-octet prefix, e.g. 172.22.0")

        start_ip = _parse_int(request.form.get("start_ip", ""), "Start IP", 2, 253)
        client_count = _parse_int(
            request.form.get("client_count", ""), "Client count", 1, 50
        )

        if start_ip + client_count - 1 > 254:
            raise ValueError(
                f"start_ip ({start_ip}) + client_count ({client_count}) would exceed .254"
            )

        allowed_nets = request.form.get("allowed_nets", "").strip()
        dns = request.form.get("dns", "").strip()
        if not dns:
            raise ValueError("DNS is required.")

    except ValueError as exc:
        return _error_partial(str(exc)), 422

    keypair = generate_keypair()

    server = ServerConfig(
        endpoint=endpoint,
        port=port,
        interface_name=interface_name,
        network=network,
        start_ip=start_ip,
        allowed_nets=allowed_nets,
        dns=dns,
        private_key=keypair["private_key"],
        public_key=keypair["public_key"],
    )
    db.session.add(server)
    db.session.commit()

    resp = make_response(
        render_template(
            "partials/server_config.html", server=server, client_count=client_count
        )
    )
    resp.headers["HX-Trigger"] = "serverGenerated"
    return resp


# ---------------------------------------------------------------------------
# POST /api/generate-clients
# ---------------------------------------------------------------------------


@api_bp.route("/generate-clients", methods=["POST"])
def generate_clients():
    try:
        server_id = _parse_int(request.form.get("server_id", ""), "server_id", 1, 2**31)
        client_count = _parse_int(
            request.form.get("client_count", ""), "Client count", 1, 50
        )
    except ValueError as exc:
        return _error_partial(str(exc)), 422

    server = ServerConfig.query.get_or_404(server_id)

    # Remove existing clients before regenerating
    ClientConfig.query.filter_by(server_id=server.id).delete()
    db.session.flush()

    clients = []
    for i in range(client_count):
        octet = server.start_ip + i
        kp = generate_keypair()
        client = ClientConfig(
            server_id=server.id,
            name=f"Client_{octet}",
            ip_octet=octet,
            private_key=kp["private_key"],
            public_key=kp["public_key"],
            preshared_key=generate_preshared_key(),
        )
        db.session.add(client)
        clients.append(client)

    db.session.commit()

    # Rebuild routeros config now that clients exist
    routeros_config = build_server_config(server, clients)

    return render_template(
        "partials/client_list.html",
        server=server,
        clients=clients,
        routeros_config=routeros_config,
    )


# ---------------------------------------------------------------------------
# GET /api/qr/<client_id>   — inline PNG for <img src>
# ---------------------------------------------------------------------------


@api_bp.route("/qr/<int:client_id>")
def qr_inline(client_id):
    client = ClientConfig.query.get_or_404(client_id)
    conf_text = build_client_config(client.server, client)
    png = generate_qr_png(conf_text)
    return Response(png, mimetype="image/png")


# ---------------------------------------------------------------------------
# GET /api/download/qr/<client_id>  — download single QR PNG
# ---------------------------------------------------------------------------


@api_bp.route("/download/qr/<int:client_id>")
def download_qr(client_id):
    client = ClientConfig.query.get_or_404(client_id)
    conf_text = build_client_config(client.server, client)
    png = generate_qr_png(conf_text)
    resp = make_response(png)
    resp.headers["Content-Type"] = "image/png"
    resp.headers["Content-Disposition"] = f'attachment; filename="{client.name}.png"'
    return resp


# ---------------------------------------------------------------------------
# GET /api/download/clients/<server_id>  — ZIP of all client .conf files
# ---------------------------------------------------------------------------


@api_bp.route("/download/clients/<int:server_id>")
def download_clients(server_id):
    server = ServerConfig.query.get_or_404(server_id)
    clients = server.clients

    routeros_config = build_server_config(server, clients)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("server_routeros.rsc", routeros_config)
        for client in clients:
            conf_text = build_client_config(server, client)
            zf.writestr(f"{client.name}.conf", conf_text)
            zf.writestr(f"{client.name}_qr.png", generate_qr_png(conf_text))

    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers["Content-Type"] = "application/zip"
    resp.headers["Content-Disposition"] = 'attachment; filename="clients.zip"'
    return resp


# ---------------------------------------------------------------------------
# GET /api/clear-clients  — empty swap target on serverGenerated event
# ---------------------------------------------------------------------------


@api_bp.route("/clear-clients")
def clear_clients():
    return ""
