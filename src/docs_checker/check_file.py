from collections import defaultdict
from datetime import datetime
import json
import os
import sys
from pathlib import Path
import logging

# Добавляем корень проекта в sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from src.data.db.base import get_db_session
from src.utils.remind import set_reminder
from src.repositories.contract_repo import ContractRepository

load_dotenv()

logging.basicConfig(filename="/Users/ddrxg/Code/ParserPDFforRemind/logs.txt", level=logging.DEBUG, format='%(asctime)s: %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv('HF_TOKEN')
HF_MODEL = "openai/gpt-oss-20b"

client = InferenceClient(
    model=HF_MODEL,
    token=HF_TOKEN
)

SYS_PROMPT = """
Ты — эксперт по анализу текста договоров. Твоя задача — проанализировать предоставленный текст чанка и определить, какие части текста соответствуют следующим полям договора:

Если поле не найдено в тексте, пропусти его. 
Формат ответа, без рассуждений и мыслей, только готовы ответ. 

1. party_1_name — имя или название первой стороны договора.
2. party_2_name — имя или название второй стороны договора.
3. contract_date — дата заключения договора.
4. contract_start — дата начала действия договора.
5. contract_end — дата окончания действия договора.
6. subject — предмет договора (товар, услуга и т.д.).
7. delivery_terms — условия доставки.
8. payment_terms — условия оплаты.
9. amount — сумма договора.
10. currency — валюта договора.
11. penalty_present — наличие неустойки (да/нет).
12. penalty_amount_or_formula — сумма неустойки или формула расчета.
13. extension_possible — возможность продления договора (да/нет).
14. extension_conditions — условия продления договора.
15. termination_conditions — условия расторжения договора.

Для каждого поля верни JSON-объект, где ключ — название поля, а значение — ID цитаты из предоставленного списка. 
Если поле не найдено в тексте, пропусти его. 
Формат ответа, без рассуждений и мыслей, только готовы ответ. 
Если подходящих цитат под одну категорию несколько, то записывай айди в виде листа через запятую:
{{
  "party_1_name": [<ID>, <ID>, <ID>],
  "party_2_name": <ID>,
  ...и так далее из всего списка полей договора.
}}
Список цитат: {citation}
"""

def llm(prompt: str, context: str | None, retries: int = 3):
    for attempt in range(retries):
        try:
            # logger.debug(f"Sending prompt (attempt {attempt + 1}): {prompt[:1000]}...")
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt, "context": context if context is not None else 'Первое сообщение, контекста нет.'}],
                max_tokens=2048,
                temperature=0.2,
                top_p=0.2,
                stream=False
            )
            content = response.choices[0].message.content.strip() # type: ignore
            return content, response
        except Exception as e:
            logger.error(f"LLM call error (attempt {attempt + 1}): {e}")
            continue
    return None


def get_and_send_to_llm(document_id: int):
    db = next(get_db_session())
    repo = ContractRepository(db)

    try:
        result = repo.get_citations_by_document(document_id)
    except:
        return {}

    data = []
    size = 0
    count = 0
    result_processing = []
    merged_dict = defaultdict(list)
    for citation in result:
        data.append(([citation.text], citation.id))
        size += len(citation.text) # type: ignore  (and count <= 20)
        if size > 900 and count <= 5:
            # Обработка чанка (очистка, фильтрация и т.д.)
            cleaned_data = [item for item in data if item[0]]  # Пример: убираем пустые строки
            if cleaned_data:
                response = None
                try:
                    content, response = llm(SYS_PROMPT.format(citation=cleaned_data), context=response if response is not None else None) # type: ignore
                    print(f"Ответ ИИ - {content}")
                    try:
                        chunk_dict = json.loads(content)
                        result_processing.append(chunk_dict)
                    except json.JSONDecodeError:
                        logger.error(f"Ошибка парсинга JSON: {content}")
                except Exception as e:
                    print(f'Ошибка - {e}')
            count += 1
            size = 0
            data = []

    for chunk_dict in result_processing:
        if not isinstance(chunk_dict, dict):
            logger.error(f"Некорректный формат в result_processing: {chunk_dict}")
            continue
        for key, value in chunk_dict.items():
            if not isinstance(value, list):
                value = [value]
            merged_dict[key].append(value)
    
    result = dict(merged_dict)
    # Получение или создание контракта
    contract = repo.get_contract_by_document(document_id)
    if not contract:
        contract = repo.create_contract(document_id, citation_data=merged_dict)
    else:
        repo.update_contract(contract.id, citation_data=merged_dict) # type: ignore

    # Удаление существующих связей перед вставкой новых
    repo.delete_citation_links(contract.id) # type: ignore

    # Сохранение связей с цитатами с удалением дубликатов
    links = []
    seen = set()  # Для отслеживания уникальных комбинаций (contract_id, citation_id)
    for field_name, id_lists in merged_dict.items():
        for id_list in id_lists:
            for citation_id in id_list:
                if (contract.id, citation_id) not in seen:
                    links.append({'citation_id': citation_id, 'field_name': field_name})
                    seen.add((contract.id, citation_id))
    if links:
        repo.bulk_create_citation_links(contract.id, links) # type: ignore

    set_reminder(result, datetime.now())

    return result

# if __name__ == "__main__":
#     document_id = 1
#     get_and_send_to_llm(document_id)