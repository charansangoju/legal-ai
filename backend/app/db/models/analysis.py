from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
class Analysis(Base):
    __tablename__="analyses"
    id: Mapped[int]=mapped_column(primary_key=True)
    document_id: Mapped[int]=mapped_column(Integer)
    result_json: Mapped[str]=mapped_column(Text)
