import os
import time
import requests
from dotenv import load_dotenv
import logging
import traceback

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

class ClothChangeAPI:
    def __init__(self):
        self.api_key = os.getenv('EACHLABS_API_KEY')
        self.flow_id = '8ea0e2c1-cd76-4ed4-b429-e56103d86715'
        self.base_url = 'https://flows.eachlabs.ai/api/v1'
        self.headers = {
            "X-API-KEY": self.api_key,
        }
        logger.info("ClothChangeAPI initialized")

    def change_cloth(self, person_image_url, cloth_image_url, cloth_type='', webhook_url=''):
        """
        Change the cloth in the person image with the provided cloth image
        
        Args:
            person_image_url (str): URL to the person image
            cloth_image_url (str): URL to the cloth image
            webhook_url (str, optional): URL for webhook notifications
            
        Returns:
            dict: API response with execution ID
        """
        try:
            logger.info(f"Starting cloth change process. Person: {person_image_url}, Cloth: {cloth_image_url}")
            
            payload = {
                "parameters": {
                    "Person": person_image_url,
                    "Cloth": cloth_image_url,
                    "clothing_type": cloth_type
                },
                "webhook_url": webhook_url
            }

            logger.debug(f"Sending request to EachLabs API")
            response = requests.post(
                f"{self.base_url}/{self.flow_id}/trigger",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully initiated cloth change. Execution ID: {result.get('execution_id', 'unknown')}")
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"API Request Error: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise
        except Exception as e:
            error_msg = f"Unexpected error in change_cloth: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise

    def get_executions(self):
        """
        Get all executions for the flow
        
        Returns:
            list: List of executions
        """
        try:
            logger.debug(f"Getting all executions for flow {self.flow_id}")
            response = requests.get(
                f"{self.base_url}/{self.flow_id}/executions",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Got {len(result)} executions")
            return result
        except Exception as e:
            error_msg = f"Error getting executions: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise

    def get_execution_details(self, execution_id):
        """
        Get details of a specific execution
        
        Args:
            execution_id (str): ID of the execution
            
        Returns:
            dict: Execution details
        """
        try:
            logger.debug(f"Getting execution details for ID: {execution_id}")
            response = requests.get(
                f"{self.base_url}/{self.flow_id}/executions/{execution_id}",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Execution status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            error_msg = f"Error getting execution details: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise

    def wait_for_execution(self, execution_id, max_retries=30, delay=5):
        """
        Wait for an execution to complete and get its results
        
        Args:
            execution_id (str): ID of the execution to check
            max_retries (int): Maximum number of times to check status
            delay (int): Delay between status checks in seconds
            
        Returns:
            dict: Execution details with results
        """
        logger.info(f"Starting to wait for execution {execution_id}")
        
        for attempt in range(max_retries):
            try:
                execution = self.get_execution_details(execution_id)
                status = execution.get('status', '').lower()
                logger.info(f"Execution {execution_id} status: {status} (attempt {attempt + 1}/{max_retries})")
                
                if status == 'succeeded':
                    logger.info(f"Execution {execution_id} completed successfully")
                    return execution
                elif status in ['failed', 'error']:
                    error_msg = f"Execution failed: {execution.get('error', 'Unknown error')}"
                    logger.error(f"Execution {execution_id} failed: {error_msg}")
                    raise Exception(error_msg)
                
                time.sleep(delay)
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Error checking execution status: {str(e)}"
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                time.sleep(delay)
        
        error_msg = f"Timeout waiting for execution {execution_id} after {max_retries} attempts"
        logger.error(error_msg)
        raise TimeoutError(error_msg)

def main():
    # Example usage
    api = ClothChangeAPI()
    
    try:
        # Replace these paths with your actual image URLs
        person_image_url = "url/to/person.jpg"
        cloth_image_url = "url/to/cloth.jpg"
        
        result = api.change_cloth(person_image_url, cloth_image_url)
        logger.info(f"API Response: {result}")
        
        execution_id = result.get('execution_id')
        if execution_id:
            execution = api.wait_for_execution(execution_id)
            logger.info(f"Execution Details: {execution}")
        
    except Exception as e:
        error_msg = f"Failed to process images: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
