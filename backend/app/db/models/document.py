from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
class Document(Base):
    __tablename__="documents"
    id: Mapped[int]=mapped_column(primary_key=True)
    filename: Mapped[str]=mapped_column(String(255))
    content: Mapped[str]=mapped_column(Text)
    doc_type: Mapped[str]=mapped_column(String(100), default="unknown")
