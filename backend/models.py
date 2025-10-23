from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)

    # Было: LONGTEXT / TEXT со строками JSON
    # Стало: нативные JSON-колонки (работают в PostgreSQL и MySQL)
    plan = Column(JSON, nullable=False, default=dict)
    detection = Column(JSON, nullable=False, default=dict)
    routes = Column(JSON, nullable=False, default=dict)
    estimate = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
