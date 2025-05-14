from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
import os
import uuid
import time
from enum import Enum
from random import choice

app = FastAPI()

VIDEO_STORAGE_DIR = "video_storage"
os.makedirs(VIDEO_STORAGE_DIR, exist_ok=True)


class AgeRestriction(str, Enum):
    AR13 = "AR13"
    AR18 = "AR18"
    UR = "UR"


def classify_video(filename: str) -> AgeRestriction:
    time.sleep(0.5)
    return choice(list(AgeRestriction))


@app.post("/upload/", status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{file_id}{file_extension}"
    file_path = os.path.join(VIDEO_STORAGE_DIR, file_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    age_restriction = classify_video(file_name)

    return {
        "filename": file_name,
        "age_restriction": age_restriction,
        "message": "Video uploaded and classified successfully",
    }


@app.get("/video/{filename}")
async def get_video(filename: str):
    file_path = os.path.join(VIDEO_STORAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type="video/mp4")


@app.get("/videos/")
async def list_videos():
    videos = os.listdir(VIDEO_STORAGE_DIR)
    return {"videos": videos}


@app.delete("/video/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(filename: str):
    file_path = os.path.join(VIDEO_STORAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")

    os.remove(file_path)
    return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
