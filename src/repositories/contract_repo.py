from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from src.data.db.models import Document, Contract, Citation, Requisites, Obligation, Reminder

class ContractRepository:
    """Репозиторий для работы с таблицами БД в проекте ObliGate"""

    def __init__(self, db: Session):
        """Инициализация с сессией БД из get_db_session"""
        self.db = db

    # CRUD для Document
    def create_document(self, filename: str, file_path: str) -> Document:
        """Создает запись о новом документе"""
        document = Document(filename=filename, file_path=file_path)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_document(self, document_id: int) -> Optional[Document]:
        """Получает документ по ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def update_document(self, document: Document, file_path: Optional[str] = None) -> Document:
        """Обновляет документ (например, upload_date и file_path)"""
        document.upload_date = datetime.now()  # type: ignore # Обновляем дату загрузки
        if file_path:
            document.file_path = file_path # type: ignore
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def get_document_by_file_path(self, file_path: str) -> Optional[Document]:
        """Получает документ по пути к файлу"""
        return self.db.query(Document).filter(Document.file_path == file_path).first()
    
    def get_document_by_filename(self, filename: str) -> Optional[Document]:
        """Получает документ по имени файла"""
        return self.db.query(Document).filter(Document.filename == filename).first()

    def get_all_documents(self) -> List[Document]:
        """Получает все документы"""
        return self.db.query(Document).all()

    def delete_document(self, document_id: int) -> bool:
        """Удаляет документ по ID"""
        document = self.get_document(document_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False

    # CRUD для Citation
    def create_citation(self, document_id: int, text: str, page: Optional[int] = None,
                       bbox: Optional[List[float]] = None, paragraph_index: Optional[int] = None,
                       run_index: Optional[int] = None) -> Citation:
        """Создает запись о цитате из документа"""
        citation = Citation(
            document_id=document_id,
            text=text,
            page=page,
            bbox=bbox,
            paragraph_index=paragraph_index,
            run_index=run_index
        )
        self.db.add(citation)
        self.db.commit()
        self.db.refresh(citation)
        return citation

    def get_citations_by_document(self, document_id: int) -> List[Citation]:
        """Получает все цитаты для документа"""
        return self.db.query(Citation).filter(Citation.document_id == document_id).all()

    # CRUD для Contract
    def create_contract(self, document_id: int, **kwargs) -> Contract:
        """Создает запись о договоре с опциональными полями из DocsInfo"""
        contract = Contract(document_id=document_id, **kwargs)
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def get_contract_by_document(self, document_id: int) -> Optional[Contract]:
        """Получает договор по ID документа"""
        return self.db.query(Contract).filter(Contract.document_id == document_id).first()

    def update_contract(self, contract_id: int, **kwargs) -> Optional[Contract]:
        """Обновляет поля договора"""
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if contract:
            for key, value in kwargs.items():
                setattr(contract, key, value)
            self.db.commit()
            self.db.refresh(contract)
            return contract
        return None

    # CRUD для Requisites
    def create_requisites(self, contract_id: int, inn_id: Optional[int] = None,
                         kpp_id: Optional[int] = None, ogrn_id: Optional[int] = None) -> Requisites:
        """Создает запись о реквизитах договора"""
        requisites = Requisites(contract_id=contract_id, inn_id=inn_id, kpp_id=kpp_id, ogrn_id=ogrn_id)
        self.db.add(requisites)
        self.db.commit()
        self.db.refresh(requisites)
        return requisites

    def get_requisites_by_contract(self, contract_id: int) -> Optional[Requisites]:
        """Получает реквизиты по ID договора"""
        return self.db.query(Requisites).filter(Requisites.contract_id == contract_id).first()

    # CRUD для Obligation
    def create_obligation(self, contract_id: int, description: str, due_date: Optional[datetime] = None,
                         citation_id: Optional[int] = None, status: str = "pending") -> Obligation:
        """Создает запись об обязательстве"""
        obligation = Obligation(
            contract_id=contract_id,
            description=description,
            due_date=due_date,
            citation_id=citation_id,
            status=status
        )
        self.db.add(obligation)
        self.db.commit()
        self.db.refresh(obligation)
        return obligation

    def get_obligations_by_contract(self, contract_id: int) -> List[Obligation]:
        """Получает все обязательства по ID договора"""
        return self.db.query(Obligation).filter(Obligation.contract_id == contract_id).all()

    def update_obligation_status(self, obligation_id: int, status: str) -> Optional[Obligation]:
        """Обновляет статус обязательства"""
        obligation = self.db.query(Obligation).filter(Obligation.id == obligation_id).first()
        if obligation:
            obligation.status = status # type: ignore
            self.db.commit()
            self.db.refresh(obligation)
            return obligation
        return None

    # CRUD для Reminder
    def create_reminder(self, obligation_id: int, remind_date: datetime, channel: str = "telegram") -> Reminder:
        """Создает запись о напоминании"""
        reminder = Reminder(obligation_id=obligation_id, remind_date=remind_date, channel=channel)
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def get_reminders_by_obligation(self, obligation_id: int) -> List[Reminder]:
        """Получает все напоминания по ID обязательства"""
        return self.db.query(Reminder).filter(Reminder.obligation_id == obligation_id).all()

    def mark_reminder_sent(self, reminder_id: int) -> Optional[Reminder]:
        """Помечает напоминание как отправленное"""
        reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.sent = True # type: ignore
            self.db.commit()
            self.db.refresh(reminder)
            return reminder
        return None