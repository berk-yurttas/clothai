# ClothAI API

A FastAPI server that provides cloth changing functionality using the EachLabs API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your EachLabs API key:
```
EACHLABS_API_KEY=your_api_key_here
```

3. Run the server:
```bash
uvicorn main:app --reload
```

## API Usage

The API has a single endpoint:

### POST /change-cloth

Upload both person and cloth images as form-data with the following keys:
- `person`: The image of the person
- `cloth`: The image of the cloth to try on

Example using curl:
```bash
curl -X POST "http://localhost:8000/change-cloth" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "person=@/path/to/person.jpg" \
  -F "cloth=@/path/to/cloth.jpg"
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
