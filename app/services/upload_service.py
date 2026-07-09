"""Supabase S3-compatible storage upload service."""

import uuid
from pathlib import Path

import boto3
from botocore.client import Config
from fastapi import UploadFile

from app.core.config import settings
from app.utils.exceptions import BadRequestException
from app.utils.file_validation import (
    validate_image_upload,
    validate_video_upload,
)


class UploadService:
    """Upload files to Supabase Storage using S3 API."""

    def __init__(self) -> None:
        self.bucket = settings.SUPABASE_S3_BUCKET_NAME

        self.client = boto3.client(
            "s3",
            endpoint_url=settings.SUPABASE_S3_ENDPOINT_URL,
            aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.SUPABASE_S3_SECRET_ACCESS_KEY,
            region_name=settings.SUPABASE_S3_REGION,
            config=Config(signature_version="s3v4"),
        )

        self.public_url = settings.SUPABASE_PROJECT_URL.rstrip(
            "/"
        ) + f"/storage/v1/object/public/{self.bucket}"


    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "images",
    ) -> str:

        contents = await file.read()

        validate_image_upload(
            file.content_type,
            len(contents),
        )

        return self._upload(
            contents,
            file.content_type,
            folder,
        )


    async def upload_video(
        self,
        file: UploadFile,
        folder: str = "videos",
    ) -> str:

        contents = await file.read()

        validate_video_upload(
            file.content_type,
            len(contents),
        )

        return self._upload(
            contents,
            file.content_type,
            folder,
        )


    def _upload(
        self,
        contents: bytes,
        content_type: str | None,
        folder: str,
    ) -> str:

        filename = f"{uuid.uuid4()}"
        
        if content_type:
            ext = content_type.split("/")[-1]
            filename += f".{ext}"

        object_path = f"{folder}/{filename}"

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_path,
                Body=contents,
                ContentType=content_type or "application/octet-stream",
            )

        except Exception as exc:
            raise BadRequestException(
                f"Upload failed: {exc}"
            )

        return f"{self.public_url}/{object_path}"


    async def delete_file(self, file_url: str) -> None:
        prefix = f"{self.public_url}/"

        if not file_url.startswith(prefix):
            return

        object_path = file_url.replace(prefix, "")

        self.client.delete_object(
            Bucket=self.bucket,
            Key=object_path,
        )