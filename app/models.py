from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text,LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    useremail = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    anki_packages = relationship("AnkiPackage", back_populates="user")

class AnkiPackage(Base):
    __tablename__ = "anki_packages"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    note_count = Column(Integer)
    deck_count = Column(Integer)
    deck_names = Column(JSON)
    language = Column(String(45), nullable=True)
    data = Column(LargeBinary, nullable=True)
    user = relationship("User", back_populates="anki_packages")
    notes = relationship("AnkiNote", back_populates="anki_package")

class AnkiNote(Base):
    __tablename__ = "anki_notes"
    id = Column(Integer, primary_key=True, index=True)
    anki_package_id = Column(Integer, ForeignKey("anki_packages.id"))
    guid = Column(Text)
    mid = Column(Text)
    mod = Column(Integer)
    usn = Column(Integer)
    tags = Column(Text)
    flds = Column(Text)
    sfld = Column(Text)
    csum = Column(Text)
    flags = Column(Integer)
    data = Column(Text)

    anki_package = relationship("AnkiPackage", back_populates="notes")

class AnkiWord(Base):
    __tablename__ = "anki_words"
    id = Column(Integer, primary_key=True, autoincrement=True)
    words = Column(Text)
    translated = Column(Text)
    language = Column(String(45), nullable=True)

class AnkiQuize(Base):
    __tablename__ = "anki_quize"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    result = Column(String(45), nullable=True)
    quizeData = Column(JSON, nullable=True)
    language = Column(String(45), nullable=True)
    user = relationship("User")
