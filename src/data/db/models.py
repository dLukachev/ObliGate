from sqlalchemy import Column, Float, Integer, String, ForeignKey, DateTime, JSON, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from src.data.db.base import Base

# Модель для связи многие-ко-многим между Contract и Citation
contract_citation_links = Table(
    'contract_citation_links', Base.metadata,
    Column('contract_id', Integer, ForeignKey('contracts.id'), primary_key=True),
    Column('citation_id', Integer, ForeignKey('citations.id'), primary_key=True),
    Column('field_name', String(50), nullable=False)  # Имя поля, например "party_1_name"
)

# Модель для документов
class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)  # Имя файла
    upload_date = Column(DateTime, default=datetime.now())  # Дата загрузки
    file_path = Column(String, nullable=True)  # Путь к файлу (если храним локально)

    # Связи
    citations = relationship("Citation", back_populates="document")
    contract = relationship("Contract", back_populates="document", uselist=False)  # Один договор на документ

# Модель для цитат
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

# Модель для реквизитов
class Requisites(Base):
    __tablename__ = 'requisites'

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    inn_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    kpp_id = Column(Integer, ForeignKey('citations.id'), nullable=True)
    ogrn_id = Column(Integer, ForeignKey('citations.id'), nullable=True)

    # Связи
    inn = relationship("Citation", foreign_keys=[inn_id])
    kpp = relationship("Citation", foreign_keys=[kpp_id])
    ogrn = relationship("Citation", foreign_keys=[ogrn_id])

    contract = relationship("Contract", back_populates="requisites")

# Модель для извлеченной информации из договора
class Contract(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, unique=True)

    citation_data = Column(JSON, nullable=True)  # {"party_1_name": [6,7,8], "contract_date": [5], ...} для аналитики

    parsed_amount = Column(Float, nullable=True)  # Парсенная сумма для удобства
    parsed_currency = Column(String, nullable=True)  # Валюта
    parsed_penalty_present = Column(Boolean, nullable=True)  # Булево для наличия штрафа

    # Связи
    document = relationship("Document", back_populates="contract")
    requisites = relationship("Requisites", back_populates="contract", uselist=False)  # Одни реквизиты на договор
    obligations = relationship("Obligation", back_populates="contract")  # Множество обязательств
    citations = relationship("Citation", secondary=contract_citation_links, back_populates="contracts")

# Модель для обязательств/дедлайнов
class Obligation(Base):
    __tablename__ = 'obligations'

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    description = Column(String, nullable=False)  # Описание обязательства
    due_date = Column(DateTime, nullable=True)  # Срок выполнения
    status = Column(String, default='pending')  # pending, completed, overdue
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

# Добавляем связь для Citation к Contract через contract_citation_links
Citation.contracts = relationship("Contract", secondary=contract_citation_links, back_populates="citations")