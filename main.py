import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cloth_change import ClothChangeAPI
import base64
import requests
from dotenv import load_dotenv
import logging
import traceback
from datetime import datetime

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

@app.post("/change-cloth")
async def change_cloth(
    person: UploadFile = File(...),
    cloth: UploadFile = File(...)
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
            cloth_image_url=cloth_url
        )
        
        logger.info(f"[{request_id}] Successfully initiated cloth change. Execution ID: {result.get('execution_id', 'unknown')}")
        return result
        
    except Exception as e:
        error_msg = f"Error processing cloth change: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
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
        return {
            "execution_id": execution_id,
            "status": status,
            "details": result
        }
        
    except Exception as e:
        error_msg = f"Error checking execution status: {str(e)}"
        logger.error(f"Error for execution {execution_id}: {error_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
