from flask import Blueprint, render_template

from app.models import ServerConfig

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/configs")
def config_list():
    servers = ServerConfig.query.order_by(ServerConfig.created_at.desc()).all()
    return render_template("config_list.html", servers=servers)


@main_bp.route("/configs/<int:server_id>")
def config_detail(server_id):
    server = ServerConfig.query.get_or_404(server_id)
    from app.services.config_builder import build_server_config
    routeros_config = build_server_config(server, server.clients)
    return render_template(
        "config_detail.html",
        server=server,
        routeros_config=routeros_config,
    )
