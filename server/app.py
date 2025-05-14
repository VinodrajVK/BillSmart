from typing import List
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import cv2
from groq import BaseModel
import numpy as np
import shutil
from ultralytics import YOLO
import uuid
import os
from fpdf import FPDF
import json

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Item(BaseModel):
    name: str
    count: int
    price: float


@app.get("/")
async def read_root():
    return {"BillSmart": "Welcome to BillSmart API"}

PRICE_LIST = {
    "Bingo Mad Angles": 20,
    "Bottle": 10,
    "Cinthol": 30,
    "Coconut water": 20,
    "Colin": 115,
    "Dark Fantasy": 50,
    "Exo Soap": 20,
    "Fanta": 45,
    "Harpic": 95,
    "India Gate - Feast Rozzana": 100,
    "Lays": 20,
    "Lotte Chocopie": 50,
    " Mixed Fruit": 90,
    "Moms magic": 10,
    "Odonil": 20,
    "Parle-G": 30,
    "Quaker Oats": 135,
    "Savlon Herbal": 165,
    "Sprit": 45,
    "Thums-up": 45,
}
MODEL_PATH = "./model_pts/XYZ Supermarket_Model.pt"
model = YOLO(MODEL_PATH, task='detect')

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure the upload directory exists
BILLS_DIR = "bills"
os.makedirs(BILLS_DIR, exist_ok=True)  # Ensure the bills directory exists


@app.post("/process_image/")
async def upload_image(file: UploadFile = File(...)):
    # Save the uploaded image temporarily
    file_ext = file.filename.split(".")[-1]
    img_path = f"{UPLOAD_DIR}/{uuid.uuid4()}.{file_ext}"

    with open(img_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read image with OpenCV
    img = cv2.imread(img_path)

    # Run YOLO object detection
    results = model(img, verbose=False)
    detections = results[0].boxes

    # Process results
    detected_items = []
    for detection in detections:
        class_id = int(detection.cls.item())
        confidence = detection.conf.item()

        if confidence > 0.5:  # Confidence threshold
            class_name = model.names[class_id]
            # Get price from the price list
            price = PRICE_LIST.get(class_name, 0)
            detected_items.append(
                {"name": class_name, "count": 1, "price": price})  # Dummy price

    # Remove the temporary file
    os.remove(img_path)

    # If no items detected, return dummy data
    if not detected_items:
        detected_items = [
            {"name": "Apple", "count": 3, "price": 50},
            {"name": "Banana", "count": 2, "price": 20},
            {"name": "Milk", "count": 1, "price": 60},
        ]

    return {"items": detected_items}


@app.post("/generate_bill/")
async def generate_bill(items: List[Item]):
    if not items:
        return {"error": "No items provided"}

    total_amount = sum(item.count * item.price for item in items)

    # Generate PDF bill
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("FreeSerif", "", "FreeSerif.ttf", uni=True)
    pdf.set_font("FreeSerif", "", 14)

    # 🔹 Shop Name Header
    pdf.cell(200, 10, "XYZ Supermarket", ln=True, align="C")
    pdf.set_font("FreeSerif", "", 12)
    pdf.cell(200, 10, "123, Market Street, City | Ph: 9876543210",
             ln=True, align="C")
    pdf.cell(200, 10, "-------------------------------------------",
             ln=True, align="C")

    # 🔹 Table Headers
    pdf.set_font("FreeSerif", "", 12)
    pdf.cell(80, 10, "Item", border=1, align="C")
    pdf.cell(40, 10, "Qty", border=1, align="C")
    pdf.cell(40, 10, "Price", border=1, align="C")
    pdf.cell(40, 10, "Total", border=1, ln=True, align="C")

    # 🔹 Table Content
    for item in items:
        pdf.cell(80, 10, item.name, border=1, align="C")
        pdf.cell(40, 10, str(item.count), border=1, align="C")
        pdf.cell(40, 10, f"₹{item.price:.2f}", border=1, align="C")
        pdf.cell(40, 10, f"₹{item.count * item.price:.2f}",
                 border=1, ln=True, align="C")

    # 🔹 Total Amount
    pdf.cell(200, 10, "-------------------------------------------",
             ln=True, align="C")
    pdf.set_font("FreeSerif", "", 14)
    pdf.cell(160, 10, "Total Amount:", border=1, align="R")
    pdf.cell(40, 10, f"₹{total_amount:.2f}", border=1, ln=True, align="C")

    # 🔹 Thank You Note
    pdf.cell(200, 10, "-------------------------------------------",
             ln=True, align="C")
    pdf.cell(200, 10, "Thank you for shopping with us!", ln=True, align="C")

    bill_path = f"./{BILLS_DIR}/bill.pdf"
    pdf.output(bill_path, "F")

    return FileResponse(bill_path, media_type="application/pdf", filename="bill.pdf")


@app.get("/download_bill/{bill_id}")
async def download_bill(bill_id: str):
    bill_path = f"{BILLS_DIR}/{bill_id}.pdf"
    if os.path.exists(bill_path):
        return FileResponse(bill_path, filename=f"Bill_{bill_id}.pdf", media_type="application/pdf")
    return {"error": "Bill not found"}


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
