from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, APIRouter
from fastapi.responses import Response
from sqlalchemy.orm import Session

from images.models import Image

from db import get_db

router = APIRouter(prefix="/images", tags=["images"])
# -------------------------
# Upload Image
# -------------------------
@router.post("/upload/")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")

    data = await file.read()

    img = Image(
        filename=file.filename,
        content_type=file.content_type,
        data=data
    )

    db.add(img)
    db.commit()
    db.refresh(img)

    return {"id": img.id, "filename": img.filename}


# -------------------------
# Get image metadata
# -------------------------
@router.get("/image/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)):
    img = db.query(Image).filter(Image.id == image_id).first()

    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    return {
        "id": img.id,
        "filename": img.filename,
        "content_type": img.content_type
    }


# -------------------------
# View image (raw bytes)
# -------------------------
@router.get("/image/{image_id}/view")
def view_image(image_id: int, db: Session = Depends(get_db)):
    img = db.query(Image).filter(Image.id == image_id).first()

    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(content=img.data, media_type=img.content_type)