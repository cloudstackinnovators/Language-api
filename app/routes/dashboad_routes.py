from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, AnkiPackage, AnkiNote, AnkiWord, AnkiQuize
from app.auth.auth_handler import get_current_user

router = APIRouter()

@router.get('/get-analizes/{language}')
def get_analizes(language: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    note_count = db.query(AnkiWord).filter(AnkiWord.language == language).count()
    packages = db.query(AnkiPackage).filter(
        AnkiPackage.user_id == user.id,
        AnkiPackage.language == language
    ).all()
    quize_count = db.query(AnkiQuize).filter(
        AnkiQuize.user_id == user.id,
        AnkiQuize.language == language
    ).count()
    # if not packages:
    #     raise HTTPException(status_code=404, detail="No Anki packages found for this user")
    deckCount = 0
    fileNames = []
    if packages:
        for pkg in packages:
            decks_json = pkg.deck_names
            import json
            decks = json.loads(decks_json) if decks_json else []
            deckCount += len(decks)
            if pkg.filename not in fileNames:
                fileNames.append(pkg.filename)

    return {"anki_note_count": note_count, "anki_deck_count": deckCount, "anki_quize_count": quize_count, "anki_files": len(fileNames)}

@router.post('/done-quize/{language}')
def done_quiz(
    language: str,
    quiz_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Process the quiz data and save results
    result = quiz_data.get("result")
    quizeData = quiz_data.get("quizeData", {})
    
    anki_quiz = AnkiQuize(user_id=current_user.id, result=result, quizeData=quizeData, language=language)
    db.add(anki_quiz)
    db.commit()
    
    return {"message": "Quiz completed successfully"}