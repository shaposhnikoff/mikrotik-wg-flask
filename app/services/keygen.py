import base64
import os

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


def generate_keypair() -> dict:
    key = X25519PrivateKey.generate()
    priv = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    pub = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return {
        "private_key": base64.b64encode(priv).decode("ascii"),
        "public_key": base64.b64encode(pub).decode("ascii"),
    }


def generate_preshared_key() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")
