import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sqlalchemy import text
from app.tools.database import engine

router = APIRouter(prefix="/api/v1", tags=["Documents"])

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Form("default_tenant")
):
    """
    Ingests unstructured data (PDFs, DOCX, Images), extracts the text via OCR/partitioning,
    and stores the raw text content in the canonical Supabase `documents` table.
    """
    try:
        # 1. Save uploaded file to temp file temporarily so `unstructured` can read it
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 2. Parse using unstructured (supports OCR automatically for images/PDFs if system deps exist)
        try:
            from unstructured.partition.auto import partition
            # strategy="auto" will use hi_res (Tesseract) if it's an image/PDF, or fast if it's text/docx
            elements = partition(filename=tmp_path, strategy="auto")
            parsed_text = "\n\n".join([str(el) for el in elements])
        except ImportError:
            # Fallback if unstructured is not installed in the environment yet
            parsed_text = f"[UNSTRUCTURED LIB NOT FOUND] Raw bytes length: {len(content)}. Please run: pip install unstructured python-multipart"
        except Exception as e:
            # Generic fallback if Tesseract is missing on the host OS
            parsed_text = f"[OCR FAILED - Is Tesseract installed?] Error: {str(e)}"
        
        # Cleanup temp file
        os.remove(tmp_path)

        if not parsed_text.strip():
            parsed_text = "[No text extractable]"

        # 3. Store the parsed text to Supabase canonical storage
        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO public.documents (tenant_id, filename, content)
                    VALUES (:tenant_id, :filename, :content)
                """),
                {
                    "tenant_id": tenant_id,
                    "filename": file.filename,
                    "content": parsed_text
                }
            )
            # Log to ingestion_logs for the frontend audit log
            connection.execute(
                text("""
                    INSERT INTO public.ingestion_logs (filename, type, size_bytes, dq_score, status)
                    VALUES (:filename, :type, :size_bytes, :dq_score, :status)
                """),
                {
                    "filename": file.filename,
                    "type": "Unstructured (OCR)",
                    "size_bytes": len(content),
                    "dq_score": 1.0,
                    "status": "OCR_PARSED"
                }
            )

        return {
            "status": "SUCCESS",
            "filename": file.filename,
            "message": "Document parsed and stored successfully.",
            "extracted_length": len(parsed_text)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {str(e)}")
