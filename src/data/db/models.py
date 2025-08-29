from sqlalchemy import Column, Float, Integer, String, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.data.db.base import Base

# Модель для документов
class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)  # Имя файла
    upload_date = Column(DateTime, default=datetime.now())  # Дата загрузки
    file_path = Column(String, nullable=True)  # Путь к файлу (если храним локально)
    # user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Если есть пользователи, FK на пользователя

    # Связи
    citations = relationship("Citation", back_populates="document")
    contract = relationship("Contract", back_populates="document", uselist=False)  # Один договор на документ (предполагаем)

# # Модель для пользователей
# class User(Base):
#     __tablename__ = 'users'

#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, nullable=False)
#     email = Column(String, unique=True, nullable=False)
#     hashed_password = Column(String, nullable=False)  # Для аутентификации
#     created_at = Column(DateTime, default=datetime.now())

#     # Связи
#     documents = relationship("Document", back_populates="user")

# Модель для цитат (трассировка к источнику)
class Citation(Base):
    __tablename__ = 'citations'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    text = Column(String, nullable=False)  # Извлеченный текст
    page = Column(Integer, nullable=True)  # Номер страницы
    bbox = Column(JSON, nullable=True)  # Координаты bounding box [x0, y0, x1, y1]
    paragraph_index = Column(Integer, nullable=True)  # Индекс параграфа
    run_index = Column(Integer, nullable=True)  # Индекс run (для более точной трассировки)

    # Связи
    document = relationship("Document", back_populates="citations")

# Модель для реквизитов (INN, KPP, OGRN)
class Requisites(Base):
    __tablename__ = 'requisites'

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    inn_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    kpp_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    ogrn_id = Column(Integer, ForeignKey('citations.id'), nullable=True)

    # Связи к цитатам
    inn = relationship("Citation", foreign_keys=[inn_id])
    kpp = relationship("Citation", foreign_keys=[kpp_id])
    ogrn = relationship("Citation", foreign_keys=[ogrn_id])

    contract = relationship("Contract", back_populates="requisites")

# Модель для извлеченной информации из договора (основная схема из DocsInfo)
class Contract(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, unique=True)  # Один договор на документ

    # Поля из DocsInfo, каждое ссылается на Citation
    party_1_name_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    party_2_name_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    contract_date_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    contract_start_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    contract_end_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    subject_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    delivery_terms_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    payment_terms_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    amount_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    currency_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    penalty_present_id = Column(Integer, ForeignKey('citations.id'), nullable=True)  # Может быть булевым, но храним как цитату
    penalty_amount_or_formula_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    extension_possible_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    extension_conditions_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    termination_conditions_id = Column(Integer, ForeignKey('citations.id'), nullable=True)

    parsed_amount = Column(Float, nullable=True)  # Парсенная сумма для удобства
    parsed_currency = Column(String, nullable=True)  # Валюта
    parsed_penalty_present = Column(Boolean, nullable=True)  # Булево для наличия штрафа

    # Связи к цитатам
    party_1_name = relationship("Citation", foreign_keys=[party_1_name_id])
    party_2_name = relationship("Citation", foreign_keys=[party_2_name_id])
    contract_date = relationship("Citation", foreign_keys=[contract_date_id])
    contract_start = relationship("Citation", foreign_keys=[contract_start_id])
    contract_end = relationship("Citation", foreign_keys=[contract_end_id])
    subject = relationship("Citation", foreign_keys=[subject_id])
    delivery_terms = relationship("Citation", foreign_keys=[delivery_terms_id])
    payment_terms = relationship("Citation", foreign_keys=[payment_terms_id])
    amount = relationship("Citation", foreign_keys=[amount_id])
    currency = relationship("Citation", foreign_keys=[currency_id])
    penalty_present = relationship("Citation", foreign_keys=[penalty_present_id])
    penalty_amount_or_formula = relationship("Citation", foreign_keys=[penalty_amount_or_formula_id])
    extension_possible = relationship("Citation", foreign_keys=[extension_possible_id])
    extension_conditions = relationship("Citation", foreign_keys=[extension_conditions_id])
    termination_conditions = relationship("Citation", foreign_keys=[termination_conditions_id])

    # Связи
    document = relationship("Document", back_populates="contract")
    requisites = relationship("Requisites", back_populates="contract", uselist=False)  # Одни реквизиты на договор
    obligations = relationship("Obligation", back_populates="contract")  # Множество обязательств

# Модель для обязательств/дедлайнов (формируем из извлеченных данных)
class Obligation(Base):
    __tablename__ = 'obligations'

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    description = Column(String, nullable=False)  # Описание обязательства
    due_date = Column(DateTime, nullable=True)  # Срок выполнения
    status = Column(String, default='pending')  # Статус: pending, completed, overdue
    citation_id = Column(Integer, ForeignKey('citations.id'), nullable=True)  # Ссылка на источник

    # Связи
    contract = relationship("Contract", back_populates="obligations")
    citation = relationship("Citation")
    reminders = relationship("Reminder", back_populates="obligation")

# Модель для напоминаний
class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True, index=True)
    obligation_id = Column(Integer, ForeignKey('obligations.id'), nullable=False)
    remind_date = Column(DateTime, nullable=False)  # Дата напоминания
    channel = Column(String, default='telegram')  # Канал: telegram, email и т.д.
    sent = Column(Boolean, default=False)  # Отправлено ли

    # Связи
    obligation = relationship("Obligation", back_populates="reminders")