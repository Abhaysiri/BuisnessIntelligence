from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.services.storage_service import StorageService


router = APIRouter(
    prefix="/storage",
    tags=["Storage"]
)


# --------------------------------------------------
# UPLOAD
# --------------------------------------------------

# @router.post("/upload")
# async def upload_file(
#     file: UploadFile = File(...)
# ):
#     try:

#         result = await StorageService.upload_file(file)

#         return {
#             "message": "File uploaded successfully",
#             "file": result
#         }

#     except ValueError as e:

#         raise HTTPException(
#             status_code=400,
#             detail=str(e)
#         )

#     except Exception as e:

#         raise HTTPException(
#             status_code=500,
#             detail=str(e)
#         )


# --------------------------------------------------
# METADATA
# --------------------------------------------------

@router.get("/metadata/{file_path:path}")
def get_file_metadata(
    file_path: str
):

    try:

        result = StorageService.get_metadata(file_path)

        if not result:

            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        return result

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------------------------
# DOWNLOAD / RETRIEVE
# --------------------------------------------------

@router.get("/download/{file_path:path}")
def download_file(
    file_path: str
):

    try:

        file_bytes = StorageService.download_file(
            file_path
        )

        if not file_bytes:

            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        filename = file_path.split("/")[-1]

        return StreamingResponse(
            BytesIO(file_bytes),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )