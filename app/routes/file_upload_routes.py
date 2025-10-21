from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.auth.auth_handler import get_current_user
from app.models import User
import os
from uuid import uuid4
from genanki import Package
import zipfile
import tempfile
import sqlite3
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AnkiPackage, AnkiNote, AnkiWord
from fastapi.responses import FileResponse
from fastapi import Body
import genanki
from pydantic import BaseModel

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/{language}")
async def upload_file(
    language: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filename = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    extract_dir = 'apkg_extract'
    if filename.endswith('.apkg'):
        try:
            # Extract all contents of the .apkg file to extract_dir/filename/
            extract_path = os.path.join(extract_dir, filename)
            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(extract_path)
            # Find any file that matches collection.anki* and is not a directory
            anki2_filename = None
            
            anki2_files = []
            for root, dirs, files in os.walk(extract_path):
                for name in files:
                    if name.startswith("collection.anki"):
                        anki2_files.append(os.path.join(root, name))
            print(language)
    
            if not anki2_files:
                analysis = {"message": ".apkg file missing collection.anki*"}
            else:
                analysis = {"processed_files": []}
                for anki2_path in anki2_files:
                    try:
                        conn = sqlite3.connect(anki2_path)
                        cursor = conn.cursor()
                        # Count notes
                        cursor.execute("SELECT COUNT(*) FROM notes")
                        note_count = cursor.fetchone()[0]
                        # Count decks (from col table, decks are in JSON in the 'decks' field)
                        cursor.execute("SELECT decks, models FROM col")
                        row = cursor.fetchone()
                        if row is None:
                            raise HTTPException(status_code=500, detail="No decks/models found in the col table")
                        decks_json = row[0]
                        models_json = row[1]
                        import json
                        decks = json.loads(decks_json)
                        deck_count = len(decks)
                        models = json.loads(models_json)
                        words_fields = []
                        for model_id, model_data in models.items():
                            for field in model_data.get("flds", []):
                                if field.get("name", "").lower() == language.lower() or field.get("name", "").lower() == "word":
                                    words_fields.append({
                                        "model_id": model_id,
                                        "model_name": model_data.get("name"),
                                        "field_name": field.get("name"),
                                        "ord": field.get("ord"),
                                    })
                        print(f"Processing {words_fields[0]['model_name']}-{words_fields[0]['ord']}")
                        # Save to MySQL
                        anki_package = AnkiPackage(
                            filename=filename,
                            user_id=current_user.id,
                            note_count=note_count,
                            deck_count=deck_count,
                            deck_names=decks_json,
                            language=language
                        )
                        db.add(anki_package)
                        db.commit()
                        db.refresh(anki_package)

                        # Extract and save notes
                        cursor.execute("SELECT guid, mid, mod, usn, tags, flds, sfld, csum, flags, data FROM notes")
                        notes_rows = cursor.fetchall()
                        wordslist = []
                        for row in notes_rows:
                            # if row[3] > 0:
                            note_id, guid, mid, fields = row[0], row[0], row[1], row[5]
                            wordField = next((wf for wf in words_fields if wf["model_id"] == str(mid)), None)
                            fields = row[5].split('\x1f')
                            if wordField:
                                ord_index = wordField["ord"]
                                word_value = fields[ord_index] if len(fields) > ord_index else ''
                                wordAnki = AnkiWord(
                                    words=word_value,
                                    translated=fields[1] if len(fields) > 1 else '',
                                    language=language
                                )
                                db.add(wordAnki)
                            else:
                                word_value = fields[0] if fields else ''
                            note = AnkiNote(
                                anki_package_id=anki_package.id,
                                guid=row[0],
                                mid=row[1],
                                mod=row[2],
                                usn=row[3],
                                tags=row[4],
                                flds=row[5],
                                sfld=row[6],
                                csum=row[7],
                                flags=row[8],
                                data=row[9]
                            )
                            db.add(note)
                        db.commit()
                        conn.close()
                        analysis["processed_files"].append({
                            "anki2_path": anki2_path,
                            "note_count": note_count,
                            "deck_count": deck_count,
                            "deck_names": [deck.get("name", "") for deck in decks.values()]
                        })
                    except Exception as e:
                        analysis["processed_files"].append({
                            "anki2_path": anki2_path,
                            "error": str(e)
                        })
            # New code block ends here
            
        except Exception as e:
            analysis = {"error": f"Failed to analyze .apkg: {str(e)}"}

    return {
        "filename": filename,
        "message": "File uploaded successfully",
        "analysis": analysis
    }

@router.get("/export/{anki_package_id}")
def export_deck(
    anki_package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch package and notes
    anki_package = db.query(AnkiPackage).filter_by(id=anki_package_id, user_id=current_user.id).first()
    if not anki_package:
        raise HTTPException(status_code=404, detail="Anki package not found")

    notes = db.query(AnkiNote).filter_by(anki_package_id=anki_package.id).all()
    if not notes:
        raise HTTPException(status_code=404, detail="No notes found for this package")

    # Create genanki deck
    deck_id = abs(hash(anki_package.id)) % (10 ** 10)
    deck = genanki.Deck(
        deck_id,
        anki_package.deck_names[0] if anki_package.deck_names else f"Exported Deck {anki_package.id}"
    )

    # Simple model (adjust fields as needed)
    model = genanki.Model(
        1607392319,
        'Simple Model',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Front}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
            },
        ]
    )

    # Add notes to deck
    for n in notes:
        fields = n.flds.split('\x1f')  # Anki fields are separated by \x1f
        front = fields[0] if len(fields) > 0 else ''
        back = fields[1] if len(fields) > 1 else ''
        note = genanki.Note(
            model=model,
            fields=[front, back]
        )
        deck.add_note(note)

    # Generate .apkg file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".apkg") as tmp_file:
        genanki.Package(deck).write_to_file(tmp_file.name)
        tmp_file_path = tmp_file.name

    # Return file as download
    return FileResponse(
        tmp_file_path,
        filename=f"{anki_package.deck_names[0] if anki_package.deck_names else 'deck'}.apkg",
        media_type="application/octet-stream"
    )

@router.get("/export-words")
def export_words_deck(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    words = db.query(AnkiWord).all()
    if not words:
        raise HTTPException(status_code=404, detail="No words found")

    # Create genanki deck
    deck_id = abs(hash(current_user.id)) % (10 ** 10)
    deck = genanki.Deck(
        deck_id,
        f"Exported Words Deck {current_user.username}"
    )

    # Simple model
    model = genanki.Model(
        1607392319,
        'Simple Model',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Front}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
            },
        ]
    )

    # Add notes from AnkiWord table
    for w in words:
        note = genanki.Note(
            model=model,
            fields=[w.words or '', w.translated or '']
        )
        deck.add_note(note)

    # Generate .apkg file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".apkg") as tmp_file:
        genanki.Package(deck).write_to_file(tmp_file.name)
        tmp_file_path = tmp_file.name

    # Return file as download
    return FileResponse(
        tmp_file_path,
        filename="anki_words_export.apkg",
        media_type="application/octet-stream"
    )

