import os
from dotenv import load_dotenv
from cloth_change import ClothChangeAPI
from image_uploader import ImageUploader

# Load environment variables
load_dotenv()

def main():
    # Initialize the APIs
    cloth_api = ClothChangeAPI()
    image_uploader = ImageUploader(os.getenv('IMGBB_API_KEY'))
    
    # Test image paths
    test_dir = "test_images"
    person_image = os.path.join(test_dir, "person.jpg")
    cloth_image = os.path.join(test_dir, "cloth.png")
    
    # Check if images exist
    if not os.path.exists(person_image):
        print("Please add a person image to test_images/person.jpg")
        return
        
    if not os.path.exists(cloth_image):
        print("Please add a cloth image to test_images/cloth.png")
        return
    
    try:
        # Upload images to ImgBB
        print("Uploading person image...")
        person_url = image_uploader.upload_image(person_image)
        print(f"Person image uploaded: {person_url}")
        
        print("\nUploading cloth image...")
        cloth_url = image_uploader.upload_image(cloth_image)
        print(f"Cloth image uploaded: {cloth_url}")
        
        # Make the cloth change API call
        print("\nTriggering new cloth change execution...")
        result = cloth_api.change_cloth(person_url, cloth_url)
        print("Execution triggered:", result)
        
        # Get execution results
        execution_id = result.get('trigger_id')
        if execution_id:
            print("\nWaiting for execution to complete...")
            execution = cloth_api.wait_for_execution(execution_id)
            print("\nFinal execution details:")
            print("Status:", execution.get('status'))
            print("Results:", execution.get('results', {}))
            if 'error' in execution:
                print("Error:", execution['error'])
            
            # Get detailed execution information
            print("\nGetting detailed execution information...")
            details = cloth_api.get_execution_details(execution_id)
            print("Execution Details:", details)
        else:
            print("No execution ID returned")
        
    except Exception as e:
        print(f"Error during process: {str(e)}")

if __name__ == "__main__":
    main()
