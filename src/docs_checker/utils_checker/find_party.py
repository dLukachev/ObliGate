import re

def _flatten_data(data):
    """Склеивает чанки в строку и строит карту символов -> id"""
    text = ""
    char_to_id = []
    for token, tid in data:
        token = token[0]
        if text:  # пробел перед новым токеном
            text += " "
            char_to_id.append(None)
        for ch in token:
            text += ch
            char_to_id.append(tid)
    return text, char_to_id


def find_parties(data):
    """
    Находит стороны договора (ИП, ООО, АО и т.д.).
    return: dict с party_1_name, party_2_name
    """
    text, char_to_id = _flatten_data(data)

    pattern = re.compile(
        r"(?:"
        r"Индивидуальный предприниматель\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.|"
        r"ИП\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2}|"
        r"(?:Общество с ограниченной ответственностью|ООО)\s+«[^»]+»|"
        r"(?:Акционерное общество|АО)\s+«[^»]+»|"
        r"(?:Публичное акционерное общество|ПАО)\s+«[^»]+»|"
        r"(?:Закрытое акционерное общество|ЗАО)\s+«[^»]+»|"
        r"(?:Федеральное государственное унитарное предприятие|ФГУП)\s+«[^»]+»|"
        r"(?:Государственное унитарное предприятие|ГУП)\s+«[^»]+»"
        r")",
        re.IGNORECASE
    )

    result = {"party_1_name": None, "party_2_name": None}

    for m in pattern.finditer(text):
        start, end = m.span()
        matched_ids = sorted(set(i for i in char_to_id[start:end] if i))
        context = text[end:end+80]

        if "Исполнитель" in context and result["party_1_name"] is None:
            result["party_1_name"] = {m.group(): matched_ids} # type: ignore
        elif "Заказчик" in context and result["party_2_name"] is None:
            result["party_2_name"] = {m.group(): matched_ids} # type: ignore

    return result


def find_dates(data):
    """
    Находит даты в договоре.
    return: list словарей {"date": "строка", "ids": [int, ...]}
    """
    text, char_to_id = _flatten_data(data)

    pattern = re.compile(
        r"\b\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4}\b"
        r"|\b\d{2}\.\d{2}\.\d{4}\b"
    )

    result = []
    for m in pattern.finditer(text):
        start, end = m.span()
        matched_ids = sorted(set(i for i in char_to_id[start:end] if i))
        result.append({m.group(): matched_ids})

    return result


def find_amounts(data):
    """
    Находит суммы денег.
    return: list словарей {"amount": "строка", "ids": [int, ...]}
    """
    text, char_to_id = _flatten_data(data)

    pattern = re.compile(r"\d[\d\s]{0,15}(?:руб\.?|рублей|₽)")
    result = []
    for m in pattern.finditer(text):
        start, end = m.span()
        matched_ids = sorted(set(i for i in char_to_id[start:end] if i))
        result.append({m.group(): matched_ids})

    return result


def find_requisites(data):
    """
    Находит реквизиты: ИНН, КПП, р/с, БИК.
    return: dict { "inn": [...], "kpp": [...], "account": [...], "bik": [...] }
    """
    text, char_to_id = _flatten_data(data)

    regexes = {
        "inn": r"\b\d{10}\b|\b\d{12}\b",
        "kpp": r"\b\d{9}\b",
        "account": r"\b\d{20}\b",
        "bik": r"\b\d{9}\b"
    }

    result = {k: [] for k in regexes}

    for key, pat in regexes.items():
        for m in re.finditer(pat, text):
            start, end = m.span()
            matched_ids = sorted(set(i for i in char_to_id[start:end] if i))
            result[key].append({m.group(): matched_ids})

    return result
