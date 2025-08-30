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
                temperature=0.55,
                top_p=0.55,
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
    for citation in result:
        data.append(([citation.text], citation.id))
        size += len(citation.text) # type: ignore  (and count <= 20)
        if size > 1500:
            # Обработка чанка (очистка, фильтрация и т.д.)
            cleaned_data = [item for item in data if item[0]]  # Пример: убираем пустые строки
            if cleaned_data:
                response = None
                try:
                    content, response = llm(SYS_PROMPT.format(citation=cleaned_data), context=response if response is not None else None) # type: ignore
                    print(f"Ответ ИИ - {content}")
                except Exception as e:
                    print(f'Ошибка - {e}')
            count += 1
            size = 0
            data = []

if __name__ == "__main__":
    document_id = 1
    get_and_send_to_llm(document_id)