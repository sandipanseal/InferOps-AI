from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.document_loader import load_upload_file_text
from app.core.rag_service import (
    clear_knowledge_base,
    delete_document,
    list_documents,
    query_knowledge,
    upload_document_to_qdrant,
)

router = APIRouter(prefix="/v1/rag", tags=["rag"])


class UploadTextRequest(BaseModel):
    document_name: str = Field(min_length=1)
    text: str = Field(min_length=1)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = 5
    document_name: str | None = None


@router.post("/upload-text")
async def upload_text(req: UploadTextRequest):
    return upload_document_to_qdrant(
        document_name=req.document_name,
        text=req.text,
        source_type="manual",
        filename=None,
    )


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    document_name: str | None = Form(default=None),
):
    try:
        loaded = await load_upload_file_text(file)

        final_document_name = (
            document_name.strip()
            if document_name and document_name.strip()
            else loaded["filename"]
        )

        result = upload_document_to_qdrant(
            document_name=final_document_name,
            text=loaded["text"],
            source_type="file",
            filename=loaded["filename"],
        )

        return {
            **result,
            "extracted_characters": loaded["characters"],
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(exc)}",
        ) from exc


@router.post("/query")
async def query_rag(req: QueryRequest):
    return query_knowledge(
        query=req.query,
        top_k=req.top_k,
        document_name=req.document_name,
    )


@router.get("/documents")
async def get_documents():
    return list_documents()


@router.delete("/documents/{document_name}")
async def remove_document(document_name: str):
    return delete_document(document_name)


@router.delete("/clear")
async def clear_all_documents():
    return clear_knowledge_base()