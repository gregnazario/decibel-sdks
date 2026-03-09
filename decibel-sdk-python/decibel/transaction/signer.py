"""Ed25519 transaction signer."""

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ed25519


class Ed25519Signer:
    """Ed25519 signer for Aptos transactions.

    Attributes:
        _private_key: Ed25519 private key
    """

    def __init__(self, private_key: bytes) -> None:
        """Initialize signer with private key.

        Args:
            private_key: 32-byte Ed25519 private key

        Raises:
            SigningError: If private key is invalid
        """
        if len(private_key) != 32:
            from ..errors import SigningError

            raise SigningError(f"Private key must be 32 bytes, got {len(private_key)}")

        self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)

    def sign(self, message: bytes) -> bytes:
        """Sign a message.

        Args:
            message: Message to sign

        Returns:
            64-byte signature
        """
        signature = self._private_key.sign(message)
        return signature

    @property
    def public_key(self) -> bytes:
        """Get public key.

        Returns:
            32-byte public key
        """
        pub_key = self._private_key.public_key()
        return pub_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def to_hex(self) -> str:
        """Get private key as hex string.

        Returns:
            Hex-encoded private key
        """
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ).hex()

    @classmethod
    def from_hex(cls, hex_str: str) -> "Ed25519Signer":
        """Create signer from hex-encoded private key.

        Args:
            hex_str: Hex-encoded private key (with or without 0x prefix)

        Returns:
            Ed25519Signer instance
        """
        stripped = hex_str.removeprefix("0x")
        if len(stripped) % 2 != 0:
            stripped = "0" + stripped
        private_key = bytes.fromhex(stripped)
        return cls(private_key)

    @classmethod
    def generate(cls) -> "Ed25519Signer":
        """Generate a new random keypair.

        Returns:
            Ed25519Signer instance with new keypair
        """
        import secrets

        private_key = secrets.token_bytes(32)
        return cls(private_key)


# Import serialization at module level
from cryptography.hazmat.primitives import serialization
