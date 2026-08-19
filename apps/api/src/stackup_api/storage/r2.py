"""Cloudflare R2 storage backend (S3-compatible, via boto3).

boto3 is synchronous; calls are offloaded to a threadpool so they don't block
the event loop. The bucket is private — objects are only ever read back
through the authorized API, never a public URL.
"""

from __future__ import annotations

from typing import Any

from starlette.concurrency import run_in_threadpool

from stackup_api.core.config import Settings


class R2Storage:
    def __init__(self, settings: Settings) -> None:
        import boto3

        self._bucket = settings.storage_bucket
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=settings.storage_endpoint,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            region_name=settings.storage_region,
        )

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await run_in_threadpool(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def get(self, key: str) -> bytes:
        obj = await run_in_threadpool(
            self._client.get_object, Bucket=self._bucket, Key=key
        )
        body: bytes = await run_in_threadpool(obj["Body"].read)
        return body

    async def delete(self, key: str) -> None:
        await run_in_threadpool(
            self._client.delete_object, Bucket=self._bucket, Key=key
        )
