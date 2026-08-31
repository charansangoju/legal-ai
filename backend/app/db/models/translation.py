from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from app.db.session import Base
class Translation(Base):
    __tablename__="translations"
    id: Mapped[int]=mapped_column(primary_key=True)
    document_id: Mapped[int]=mapped_column(Integer)
    language: Mapped[str]=mapped_column(String(20))
    content: Mapped[str]=mapped_column(Text)
