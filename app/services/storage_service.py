from app.db.supabase import supabase


class StorageService:

    BUCKET_NAME = "raw-data"

    @staticmethod
    async def upload_file(file):

        if not file.filename:
            raise ValueError("Filename is required")

        file_bytes = await file.read()

        if not file_bytes:
            raise ValueError("Uploaded file is empty")

        response = supabase.storage.from_(
            StorageService.BUCKET_NAME
        ).upload(
            file.filename,
            file_bytes,
            {
                "content-type": file.content_type
                or "application/octet-stream"
            }
        )

        return {
            "bucket": StorageService.BUCKET_NAME,
            "path": file.filename,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_bytes)
        }

    @staticmethod
    def get_metadata(file_path: str):

        # Separate folder and filename
        if "/" in file_path:
            directory, filename = file_path.rsplit("/", 1)
        else:
            directory = ""
            filename = file_path

        files = supabase.storage.from_(
            StorageService.BUCKET_NAME
        ).list(directory)

        for file in files:
            if file.get("name") == filename:
                return {
                    "bucket": StorageService.BUCKET_NAME,
                    "path": file_path,
                    "filename": file.get("name"),
                    "size": file.get("metadata", {}).get("size"),
                    "content_type": file.get("metadata", {}).get(
                        "mimetype"
                    ),
                    "created_at": file.get("created_at"),
                    "updated_at": file.get("updated_at")
                }

        return None

    @staticmethod
    def download_file(file_path: str):

        response = supabase.storage.from_(
            StorageService.BUCKET_NAME
        ).download(file_path)

        return response