"""
Unified storage abstraction — local filesystem or Cloudflare R2 (S3-compatible).
Selected via STORAGE_BACKEND env var ("local" | "r2").

R2 is S3-compatible, so the same boto3 code works with a custom endpoint_url.
Zero egress fees. 10 GB free forever.
"""
import logging
from pathlib import Path
from typing import BinaryIO, Union

# boto3 is imported lazily inside R2Storage to avoid crashing in
# development environments where it may not be installed.

from app.core.config import settings

logger = logging.getLogger(__name__)


class LocalStorage:
    """Store files on the local filesystem (development)."""

    def upload(self, file_obj: Union[BinaryIO, bytes], key: str) -> str:
        path = Path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = file_obj.read() if hasattr(file_obj, "read") else file_obj
        with open(path, "wb") as f:
            f.write(data)
        return str(path)

    def download(self, key: str) -> bytes:
        return Path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = Path(key)
        if path.exists():
            path.unlink()

    def get_url(self, key: str) -> str:
        return str(Path(key))

    def exists(self, key: str) -> bool:
        return Path(key).exists()


class R2Storage:
    """
    Store files in Cloudflare R2 (S3-compatible, zero egress).
    Works with boto3 by setting a custom endpoint_url.
    """

    def __init__(self):
        import boto3

        self.bucket = settings.R2_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self.public_url_base = settings.R2_PUBLIC_URL

    def upload(self, file_obj: Union[BinaryIO, bytes], key: str) -> str:
        data = file_obj.read() if hasattr(file_obj, "read") else file_obj
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)
        logger.info("Uploaded %s to r2://%s/%s", key, self.bucket, key)
        return f"r2://{self.bucket}/{key}"

    def download(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> None:
        from botocore.exceptions import ClientError

        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info("Deleted r2://%s/%s", self.bucket, key)
        except ClientError as e:
            logger.warning("Failed to delete r2://%s/%s: %s", self.bucket, key, e)

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def get_public_url(self, key: str) -> str:
        """Return the public R2 URL (if bucket has public access)."""
        if self.public_url_base:
            return f"{self.public_url_base}/{key}"
        return self.get_presigned_url(key)

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False


# Module-level singleton to avoid re-creating clients on every call
_storage_instance = None


def get_storage():
    """Factory: returns the appropriate storage backend (cached singleton)."""
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    backend = getattr(settings, "STORAGE_BACKEND", "local")
    if backend == "r2":
        _storage_instance = R2Storage()
    else:
        _storage_instance = LocalStorage()

    return _storage_instance
