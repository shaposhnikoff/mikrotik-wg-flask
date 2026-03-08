from datetime import datetime

from app import db


class ServerConfig(db.Model):
    __tablename__ = "server_configs"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    interface_name = db.Column(db.String(64), nullable=False)
    network = db.Column(db.String(16), nullable=False)  # "172.22.0"
    start_ip = db.Column(db.Integer, nullable=False)  # first client octet
    allowed_nets = db.Column(db.Text, nullable=False)  # "192.168.1.0/24,..."
    dns = db.Column(db.String(64), nullable=False)
    private_key = db.Column(db.String(64), nullable=False)
    public_key = db.Column(db.String(64), nullable=False)

    clients = db.relationship(
        "ClientConfig", backref="server", cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f"<ServerConfig {self.endpoint}:{self.port}>"


class ClientConfig(db.Model):
    __tablename__ = "client_configs"

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(
        db.Integer, db.ForeignKey("server_configs.id"), nullable=False
    )
    name = db.Column(db.String(128), nullable=False)
    ip_octet = db.Column(db.Integer, nullable=False)
    private_key = db.Column(db.String(64), nullable=False)
    public_key = db.Column(db.String(64), nullable=False)
    preshared_key = db.Column(db.String(64), nullable=False)

    @property
    def ip_address(self):
        return f"{self.server.network}.{self.ip_octet}"

    def __repr__(self):
        return f"<ClientConfig {self.name} ({self.ip_address})>"
