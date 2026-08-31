from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from app.db.session import Base
class Conversation(Base):
    __tablename__="conversations"
    id: Mapped[int]=mapped_column(primary_key=True)
    document_id: Mapped[int]=mapped_column(Integer)
    question: Mapped[str]=mapped_column(Text)
    answer: Mapped[str]=mapped_column(Text)
