from fastapi import APIRouter, File, UploadFile, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import os
import shutil
from src.data.db.base import get_db_session
from src.repositories.contract_repo import ContractRepository
from src.utils.celery_tasks import process_document

router = APIRouter()

@router.get("/")
async def test_live():
    return JSONResponse({'status': 'Working!'}, 200)

UPLOAD_DIR = "/Users/ddrxg/Code/ParserPDFforRemind/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/documents")
async def claim_docs(files: list[UploadFile] = File(...), db: Session = Depends(get_db_session)):
    saved = []
    document_ids = []

    repo = ContractRepository(db)
    for file in files:
        # Проверяем, существует ли запись по filename
        existing_document = repo.get_document_by_filename(filename=file.filename) # type: ignore
        
        if existing_document:
            # Если существует: перезаписываем файл по существующему file_path и обновляем запись
            file_path = existing_document.file_path
            with open(file_path, "wb") as buffer: # type: ignore
                shutil.copyfileobj(file.file, buffer)
            repo.update_document(existing_document)
            saved.append(file_path)
            document_ids.append(existing_document.id)
        else:
            # Если не существует: создаем новый файл и запись
            file_path = os.path.join(UPLOAD_DIR, file.filename) # type: ignore
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            document = repo.create_document(filename=file.filename, file_path=file_path) # type: ignore
            saved.append(file_path)
            document_ids.append(document.id)

        # Отправляем задачу в очередь Celery
        process_document.delay(document_ids[-1], file_path) # type: ignore

    return JSONResponse(content={"saved": saved, "document_ids": document_ids}, status_code=201)