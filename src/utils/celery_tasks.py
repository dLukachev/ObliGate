import os
import logging

from src.utils.celery_client import app
from src.utils.redis_client import get_redis_session

from src.data.db.base import get_db_session
from src.repositories.contract_repo import ContractRepository

import pymupdf
from docx import Document

@app.task
async def async_set_redis(key: str, value: str, expire: int = 10):
    async with get_redis_session() as redis:
        await redis.set(key, value, ex=expire)
        return await redis.get(key)
    
@app.task
def process_document(document_id: int, file_path: str):
    db = next(get_db_session())
    repo = ContractRepository(db)

    # Проверка существования файла
    if not os.path.exists(file_path):
        logging.error(f"Файл {file_path} не найден")
        return None

    file_extension = os.path.splitext(file_path)[1].lower()
    logging.info(f"Обработка файла с расширением: {file_extension}")

    if file_extension == ".pdf":
        try:
            doc = pymupdf.open(file_path)
            logging.info(f"Открыт PDF: {file_path}, страниц: {len(doc)}")
            full_text = ""

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text_accum = ""  # текст для текущей страницы

                blocks = page.get_text("dict")["blocks"] # type: ignore
                for block in blocks:
                    if block["type"] == 0:  # текстовый блок
                        for line in block["lines"]:
                            for span in line["spans"]:
                                span_text = span["text"].strip()
                                if span_text:  # пропускаем пустые спаны
                                    bbox = span["bbox"]
                                    page_text_accum += span_text + " "
                                    repo.create_citation(
                                        document_id=document_id,
                                        text=span_text,
                                        page=page_num,
                                        bbox=bbox,
                                        paragraph_index=0,
                                        run_index=0
                                    )

                full_text += page_text_accum + "\n"
                logging.info(f"Страница {page_num + 1}: извлечено {len(page_text_accum)} символов")

            doc.close()
            logging.info(f"Закрыт документ. Всего извлечено символов: {len(full_text)}")
            return full_text

        except Exception as e:
            logging.error(f"Ошибка при чтении PDF {file_path}: {type(e).__name__}: {str(e)}")
            return None

    elif file_extension == ".docx":
        try:
            doc = Document(file_path)
            full_text = ""
            paragraph_index = 0

            for paragr in doc.paragraphs:
                par_text = paragr.text  # сохраняем текст абзаца как есть
                full_text += par_text + "\n"  # перенос строки после абзаца

                # создаем запись для каждого абзаца
                if par_text == '':
                    pass
                else:
                    repo.create_citation(
                        document_id=document_id,
                        text=par_text,
                        page=0,  # для Word страницы обычно нет, можно 0 или вычислять по need
                        bbox=None,  # bbox для Word не нужен, оставляем None
                        paragraph_index=paragraph_index,
                        run_index=0
                    )
                paragraph_index += 1

            logging.info(f"Извлечен текст из DOCX длиной: {len(full_text)} символов")
            return full_text

        except Exception as e:
            logging.error(f"Ошибка при чтении DOCX {file_path}: {type(e).__name__}: {str(e)}")
            return None
