import os
import requests

class ImageUploader:
    def __init__(self, api_key):
        """
        Initialize ImageUploader with ImgBB API key
        
        Args:
            api_key (str): ImgBB API key
        """
        self.api_key = api_key
        self.upload_url = "https://api.imgbb.com/1/upload"
    
    def upload_image(self, image_path):
        """
        Upload an image to ImgBB
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: URL of the uploaded image
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        try:
            with open(image_path, 'rb') as image_file:
                files = {'image': image_file}
                params = {'key': self.api_key}
                
                response = requests.post(
                    self.upload_url,
                    params=params,
                    files=files
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get('success'):
                    return result['data']['url']
                else:
                    raise Exception(f"Failed to upload image: {result.get('error', {}).get('message', 'Unknown error')}")
                    
        except Exception as e:
            raise Exception(f"Failed to upload image {image_path}: {str(e)}")
