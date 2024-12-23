from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.orm import Session
from io import BytesIO

# Database connection setup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

SQLALCHAMY_DATABASE_URL = "sqlite:///./user.db"
engine = create_engine(SQLALCHAMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define the FastAPI app
app = FastAPI()

# Define the PDFFile model
class PDFFile(Base):
    __tablename__ = "pdf_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    content = Column(LargeBinary)

# Create database tables
Base.metadata.create_all(bind=engine)

# Endpoint to upload PDF
@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    
    file_content = await file.read()
    new_pdf = PDFFile(filename=file.filename, content=file_content)
    
    db.add(new_pdf)
    db.commit()
    db.refresh(new_pdf)
    
    return {"message": "PDF uploaded successfully", "file_id": new_pdf.id}

# Endpoint to retrieve PDF
@app.get("/download/{file_id}")
def download_pdf(file_id: int, db: Session = Depends(get_db)):
    pdf_file = db.query(PDFFile).filter(PDFFile.id == file_id).first()
    if not pdf_file:
        raise HTTPException(status_code=404, detail="PDF not found.")
    
    # Create a streaming response from in-memory content
    return StreamingResponse(
        BytesIO(pdf_file.content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={pdf_file.filename}"}
    )
