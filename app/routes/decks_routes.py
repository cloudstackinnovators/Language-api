from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import AnkiPackage, User, AnkiWord
from app.auth.auth_handler import get_current_user

router = APIRouter()

class AnkiWordCreate(BaseModel):
    words: str
    translated: str

@router.get("/anki-decks")
def get_anki_decks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    packages = db.query(AnkiPackage).filter(AnkiPackage.user_id == current_user.id).all()
    if not packages:
        raise HTTPException(status_code=404, detail="No Anki packages found for this user")
    return [
        {
            "id": pkg.id,
            "filename": pkg.filename,
            "note_count": pkg.note_count,
            "deck_count": pkg.deck_count,
            "deck_names": pkg.deck_names,
        }
        for pkg in packages
    ]

@router.get("/get-all-words/{language}")
def get_all_words(
    language: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    words = db.query(AnkiWord).filter(AnkiWord.language == language).all()
    if not words:
        raise HTTPException(status_code=404, detail="No words found")
    return [{"id": word.id, "words": word.words, "translated": word.translated} for word in words]

@router.get("/get-all-words-only")
def get_all_words_only(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    words = db.query(AnkiWord.words).all()
    if not words:
        raise HTTPException(status_code=404, detail="No words found")
    return words

@router.post("/add-word/{language}")
def add_word(
    language: str,
    word: AnkiWordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_word = AnkiWord(words=word.words, translated=word.translated, language=language)
    db.add(new_word)
    db.commit()
    db.refresh(new_word)
    return {"id": new_word.id, "words": new_word.words, "translated": new_word.translated}