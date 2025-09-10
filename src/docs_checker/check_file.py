from collections import defaultdict
import re
import sys
from pathlib import Path
import logging

# Добавляем корень проекта в sys.path для тестировочного запуска
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from dotenv import load_dotenv
from src.data.db.base import get_db_session
# from src.utils.remind import set_reminder
from src.repositories.contract_repo import ContractRepository

from src.docs_checker.utils_checker import find_party

load_dotenv()

logging.basicConfig(filename="/Users/ddrxg/Code/ParserPDFforRemind/logs.txt", level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_and_send_processing(document_id: int):
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
    not_find = False
    for citation in result:
        data.append(([citation.text], citation.id))
        size += len(citation.text) # type: ignore  (and count <= 20)
        if size > 900:
            cleaned_data = [item for item in data if item[0]]  # Пример: убираем пустые строки
            if cleaned_data:
                try:
                    # TODO обработка документа
                    # Данные поступают в виде [([строка], айди цитаты)], ([], int), ... ]
                    # пример возвращаемых данных
                    # "party_1_name": [<ID>, <ID>, <ID>],
                    # "party_2_name": <ID>,

                    result_skleiki = ''
                    # склеиваем в строку
                    for item in cleaned_data:
                        result_skleiki += str(f" {item[0][0]}")

                    if not_find is False:
                        party_1_2 = find_party.find_parties(cleaned_data)
                        if isinstance(party_1_2.get('party_1_name'), dict) and isinstance(party_1_2.get('party_2_name'), dict):
                            result_processing.append(party_1_2.get('party_1_name'))
                            result_processing.append(party_1_2.get('party_2_name'))
                            not_find = True

                    
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

    # set_reminder(result, datetime.now())

    return result

if __name__ == "__main__":
    get_and_send_processing(2)