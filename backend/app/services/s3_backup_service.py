import os
from pathlib import Path
from typing import Any

import boto3


BACKUP_TYPE_TO_S3_FOLDER = {
    "FULL": "full",
    "DIFF": "diff",
    "INC": "inc",
    "PRE_DEPLOY": "pre_deploy",
    "PRE_TEST": "pre_test",
    "PRE_IMPORT": "pre_import",
}

ALLOWED_BACKUP_EXTENSIONS = (".bak", ".dump", ".dmp", ".zip", ".tar", ".gz", ".log")


def normalize_s3_prefix(prefix: str | None) -> str:
    if not prefix:
        return ""

    clean_prefix = prefix.strip().strip("/")
    if not clean_prefix:
        return ""

    return f"{clean_prefix}/"


def get_backup_folder(backup_type: str) -> str:
    normalized_type = backup_type.strip().upper()

    if normalized_type not in BACKUP_TYPE_TO_S3_FOLDER:
        raise ValueError(
            "Tipo de backup no soportado. Usa FULL, DIFF, INC, "
            "PRE_DEPLOY, PRE_TEST o PRE_IMPORT."
        )

    return BACKUP_TYPE_TO_S3_FOLDER[normalized_type]


def get_s3_client():
    region = os.getenv("AWS_REGION", "us-east-2")

    client_kwargs = {
        "region_name": region
    }

    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    if access_key and secret_key:
        client_kwargs["aws_access_key_id"] = access_key
        client_kwargs["aws_secret_access_key"] = secret_key

    return boto3.client("s3", **client_kwargs)


def build_s3_key(file_name: str, backup_type: str) -> str:
    base_prefix = normalize_s3_prefix(os.getenv("AWS_BACKUP_PREFIX", ""))
    folder = get_backup_folder(backup_type)
    clean_file_name = Path(file_name).name

    return f"{base_prefix}{folder}/{clean_file_name}"


def build_s3_url(bucket: str, region: str, key: str) -> str:
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def upload_backup_to_s3(
    local_file_path: str,
    backup_type: str,
    file_name: str | None = None,
) -> dict[str, Any]:
    bucket = os.getenv("AWS_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-2")

    if not bucket:
        return {
            "status": "FAILED",
            "url": None,
            "s3_key": None,
            "folder": None,
            "error": "AWS_BUCKET no está configurado en el archivo .env"
        }

    local_path = Path(local_file_path)

    if not local_path.exists() or not local_path.is_file():
        return {
            "status": "FAILED",
            "url": None,
            "s3_key": None,
            "folder": None,
            "error": f"No existe el archivo físico de backup: {local_file_path}"
        }

    try:
        folder = get_backup_folder(backup_type)
        s3_key = build_s3_key(file_name or local_path.name, backup_type)
        s3 = get_s3_client()

        s3.upload_file(
            Filename=str(local_path),
            Bucket=bucket,
            Key=s3_key,
            ExtraArgs={
                "ServerSideEncryption": "AES256"
            }
        )

        remote_object = s3.head_object(
            Bucket=bucket,
            Key=s3_key
        )

        local_size = local_path.stat().st_size
        remote_size = remote_object.get("ContentLength", 0)

        if local_size != remote_size:
            return {
                "status": "FAILED",
                "url": None,
                "s3_key": s3_key,
                "folder": folder,
                "error": "El tamaño del archivo en S3 no coincide con el archivo local"
            }

        return {
            "status": "SUCCESS",
            "url": build_s3_url(bucket, region, s3_key),
            "s3_key": s3_key,
            "folder": folder,
            "size_bytes": remote_size,
            "error": None
        }

    except Exception as exc:
        return {
            "status": "FAILED",
            "url": None,
            "s3_key": None,
            "folder": None,
            "error": str(exc)
        }


def find_latest_backup_in_s3() -> dict[str, Any] | None:
    bucket = os.getenv("AWS_BUCKET")

    if not bucket:
        raise ValueError("AWS_BUCKET no está configurado en el archivo .env")

    base_prefix = normalize_s3_prefix(os.getenv("AWS_BACKUP_PREFIX", ""))
    s3 = get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    latest_object = None

    allowed_folders = set(BACKUP_TYPE_TO_S3_FOLDER.values())

    for page in paginator.paginate(Bucket=bucket, Prefix=base_prefix):
        for obj in page.get("Contents", []):
            key = obj.get("Key", "")

            if not key or key.endswith("/") or obj.get("Size", 0) <= 0:
                continue

            relative_key = key.removeprefix(base_prefix)
            folder = relative_key.split("/", 1)[0]
            suffix = Path(relative_key).suffix.lower()

            if folder not in allowed_folders:
                continue

            if suffix not in ALLOWED_BACKUP_EXTENSIONS:
                continue

            if latest_object is None or obj["LastModified"] > latest_object["LastModified"]:
                latest_object = obj

    return latest_object
