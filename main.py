import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from cloth_change import ClothChangeAPI
import base64
import requests
from dotenv import load_dotenv
import logging
import traceback
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db, DeviceTryCount
from pydantic import BaseModel
from typing import Optional
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="ClothAI API", description="API for cloth changing service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the ClothChangeAPI
cloth_change_api = ClothChangeAPI()
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')

class TryCountRequest(BaseModel):
    device_id: str
    try_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device123",
                "try_count": 3
            }
        }

async def upload_to_imgbb(file: UploadFile) -> str:
    """Upload an image to ImgBB and return the URL"""
    try:
        logger.info(f"Starting upload to ImgBB for file: {file.filename}")
        
        # Read file content
        contents = await file.read()
        
        # Encode to base64
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Upload to ImgBB
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64_image,
        }
        
        logger.debug("Sending request to ImgBB API")
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        # Get the image URL
        result = response.json()
        image_url = result["data"]["url"]
        logger.info(f"Successfully uploaded image to ImgBB: {image_url}")
        return image_url
        
    except Exception as e:
        error_msg = f"Failed to upload image: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

# API Key security
API_KEY = os.getenv('MOBILE_API_KEY', 'your_mobile_api_key')  # Set this in .env file
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

@app.post("/change-cloth")
async def change_cloth(
    person: UploadFile = File(...),
    cloth: UploadFile = File(...),
    clothing_type: str = "",
    api_key: str = Depends(verify_api_key)
):
    """
    Change cloth in the person image with the provided cloth image.
    Both images should be uploaded as form-data with keys 'person' and 'cloth'.
    """
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.info(f"[{request_id}] New cloth change request received")
    if not person.content_type.startswith("image/"):
        error_msg = "Person file must be an image"
        logger.error(f"[{request_id}] Validation error: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    if not cloth.content_type.startswith("image/"):
        error_msg = "Cloth file must be an image"
        logger.error(f"[{request_id}] Validation error: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        logger.info(f"[{request_id}] Uploading person image: {person.filename}")
        person_url = await upload_to_imgbb(person)
        
        logger.info(f"[{request_id}] Uploading cloth image: {cloth.filename}")
        cloth_url = await upload_to_imgbb(cloth)
        
        logger.info(f"[{request_id}] Processing cloth change")
        result = cloth_change_api.change_cloth(
            person_image_url=person_url,
            cloth_image_url=cloth_url,
            clothing_type=clothing_type
        )
        
        logger.info(f"[{request_id}] Successfully initiated cloth change. Execution ID: {result.get('execution_id', 'unknown')}")
        return result
        
    except Exception as e:
        error_msg = f"Error processing cloth change: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/status/{execution_id}")
async def get_execution_status(
    execution_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get the status of a cloth change execution.
    
    Args:
        execution_id: The ID of the execution to check
        
    Returns:
        dict: Execution details including status and results if available
    """
    logger.info(f"Status check requested for execution: {execution_id}")
    
    try:
        result = cloth_change_api.get_execution_details(execution_id)
        status = result.get('status', '').lower()
        
        logger.info(f"Status for execution {execution_id}: {status}")
        if status == 'succeeded':
            logger.info(f"Execution {execution_id} completed successfully")
            output_url = result.get('output', '')
            logger.info(result)
            if output_url:
                output_url = output_url.replace('"', '')
                logger.info(f"Output URL: {output_url}")
                
                # Download the image
                response = requests.get(output_url)
                response.raise_for_status()
                
                # Create a temporary UploadFile
                temp_file = UploadFile(
                    filename=f"output_{execution_id}.png",
                    file=io.BytesIO(response.content)
                )
                
                # Upload to ImgBB
                imgbb_url = await upload_to_imgbb(temp_file)
                logger.info(f"Output image uploaded to ImgBB: {imgbb_url}")
                result['output_url'] = imgbb_url
                
        return {
            "execution_id": execution_id,
            "status": status,
            "details": result
        }
        
    except Exception as e:
        error_msg = f"Error checking execution status: {str(e)}"
        logger.error(f"Error for execution {execution_id}: {error_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/try-count/{device_id}")
async def get_try_count(
    device_id: str, 
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get the remaining try count for a device"""
    device = db.query(DeviceTryCount).filter(DeviceTryCount.device_id == device_id).first()
    if not device:
        return {"device_id": device_id, "try_count_left": None}
    return {"device_id": device_id, "try_count_left": device.try_count_left}

@app.post("/try-count")
async def update_try_count(request: TryCountRequest, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Update try count for a device"""
    try:
        device = db.query(DeviceTryCount).filter(DeviceTryCount.device_id == request.device_id).first()
        
        if not device:
            device = DeviceTryCount(
                device_id=request.device_id, 
                try_count_left=request.try_count
            )
            db.add(device)
        else:
            device.try_count_left = request.try_count
        
        device.last_updated = datetime.utcnow()
        db.commit()
        return {"device_id": request.device_id, "try_count_left": device.try_count_left}
    except Exception as e:
        logger.error(f"Error updating try count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices")
async def get_devices(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get all devices"""
    return db.query(DeviceTryCount).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
