from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Проект")
    plan_json: Mapped[str] = mapped_column(LONGTEXT)
    detection_json: Mapped[str] = mapped_column(LONGTEXT)
    routes_json: Mapped[str] = mapped_column(LONGTEXT)
    estimate_json: Mapped[str] = mapped_column(LONGTEXT)
