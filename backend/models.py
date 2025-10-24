# models.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, func, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database import Base

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    mimetype = Column(String(64), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    data = Column(LargeBinary, nullable=False)  # храним байты файла (PNG/JPG/SVG)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)

    # нативные JSON-поля (универсально для Postgres/MySQL)
    plan = Column(JSON, nullable=False, default=dict)        # гео-объекты/стены/масштаб (если нужно)
    detection = Column(JSON, nullable=False, default=dict)
    routes = Column(JSON, nullable=False, default=dict)
    estimate = Column(JSON, nullable=False, default=dict)

    # ссылка на загруженный план (картинку)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    plan_ref = relationship("Plan")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
