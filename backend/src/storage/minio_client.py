"""
MinIO client for S3-compatible object storage.
Stores PDFs and generated reports. Mirrors AWS S3 for easy migration.
"""
import io
from typing import Optional
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MinIOClient:
    """S3-compatible object storage client using MinIO."""

    def __init__(self):
        """Initialize MinIO client and ensure buckets exist."""
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket_papers = settings.minio_bucket_papers
        self.bucket_reports = settings.minio_bucket_reports
        logger.info(f"MinIOClient initialized: endpoint={settings.minio_endpoint}")

    def ensure_buckets(self) -> None:
        """Create required buckets if they don't exist."""
        for bucket in [self.bucket_papers, self.bucket_reports]:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
                else:
                    logger.debug(f"MinIO bucket exists: {bucket}")
            except S3Error as e:
                logger.error(f"Failed to create bucket '{bucket}': {e}")
                raise

    def upload_pdf(self, paper_id: str, pdf_content: bytes) -> str:
        """
        Upload a PDF to the papers bucket.

        Args:
            paper_id: Unique paper identifier (used as object key)
            pdf_content: Raw PDF bytes

        Returns:
            Object path in MinIO (e.g., 'papers/2301.00001.pdf')
        """
        object_name = f"{paper_id}.pdf"
        try:
            self.client.put_object(
                bucket_name=self.bucket_papers,
                object_name=object_name,
                data=io.BytesIO(pdf_content),
                length=len(pdf_content),
                content_type="application/pdf",
            )
            path = f"{self.bucket_papers}/{object_name}"
            logger.info(f"Uploaded PDF: {path} ({len(pdf_content)} bytes)")
            return path
        except S3Error as e:
            logger.error(f"Failed to upload PDF '{paper_id}': {e}")
            raise

    def upload_report(self, report_id: str, markdown_content: str) -> str:
        """
        Upload a generated report to the reports bucket.

        Args:
            report_id: Unique report identifier
            markdown_content: Report markdown text

        Returns:
            Object path in MinIO
        """
        object_name = f"{report_id}.md"
        content_bytes = markdown_content.encode("utf-8")
        try:
            self.client.put_object(
                bucket_name=self.bucket_reports,
                object_name=object_name,
                data=io.BytesIO(content_bytes),
                length=len(content_bytes),
                content_type="text/markdown",
            )
            path = f"{self.bucket_reports}/{object_name}"
            logger.info(f"Uploaded report: {path}")
            return path
        except S3Error as e:
            logger.error(f"Failed to upload report '{report_id}': {e}")
            raise

    def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download a file from MinIO."""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Failed to download {bucket}/{object_name}: {e}")
            raise

    def get_presigned_url(
        self, bucket: str, object_name: str, expires: int = 3600
    ) -> str:
        """Get a presigned URL for temporary access to an object."""
        try:
            return self.client.presigned_get_object(
                bucket, object_name, expires=timedelta(seconds=expires)
            )
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def list_objects(self, bucket: str, prefix: Optional[str] = None) -> list:
        """List objects in a bucket with optional prefix filter."""
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [{"name": obj.object_name, "size": obj.size} for obj in objects]
        except S3Error as e:
            logger.error(f"Failed to list objects in '{bucket}': {e}")
            raise
