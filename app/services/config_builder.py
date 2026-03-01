"""
Build RouterOS CLI commands and WireGuard .conf text from model objects.
"""


def build_server_config(server, clients) -> str:
    """
    Return paste-ready MikroTik RouterOS CLI commands for the given server + clients.
    """
    lines = []

    lines.append("/interface wireguard")
    lines.append(
        f'add listen-port={server.port} mtu=1420 name={server.interface_name} private-key="{server.private_key}"'
    )
    lines.append("")
    lines.append("/ip firewall filter")
    lines.append(
        f'add action=accept chain=input comment="Allow Wireguard from All" dst-port={server.port} protocol=udp'
    )
    lines.append(
        f'add action=accept chain=input comment="Allow DNS from Wireguard Users" dst-port=53 in-interface={server.interface_name} protocol=udp'
    )
    lines.append("")
    lines.append("/ip address")
    lines.append(
        f'add address={server.network}.1/24 comment="Wireguard Interface" interface={server.interface_name} network={server.network}.0'
    )
    lines.append("")
    lines.append("/interface wireguard peers")
    for client in clients:
        lines.append(
            f'add allowed-address={server.network}.{client.ip_octet}/32 comment="{client.name}" '
            f"endpoint-address={server.network}.{client.ip_octet} interface={server.interface_name} "
            f'public-key="{client.public_key}" preshared-key="{client.preshared_key}"'
        )

    return "\n".join(lines)


def build_client_config(server, client) -> str:
    """
    Return a standard WireGuard .conf INI string for a single client.
    """
    allowed_ips = f"{server.network}.1/32"
    if server.allowed_nets:
        allowed_ips += f",{server.allowed_nets}"

    lines = [
        "[Interface]",
        f"## {client.name}",
        f"Address = {server.network}.{client.ip_octet}/32",
        f"PrivateKey = {client.private_key}",
        f"DNS = {server.dns}",
        "",
        "[Peer]",
        f"PublicKey = {server.public_key}",
        f"PreSharedKey = {client.preshared_key}",
        f"AllowedIPs = {allowed_ips}",
        f"Endpoint = {server.endpoint}:{server.port}",
        "PersistentKeepalive = 10",
    ]
    return "\n".join(lines)
