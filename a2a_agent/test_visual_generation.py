import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_ideogram():
    """Test Ideogram API directly"""
    import requests
    
    api_key = os.environ.get("IDEOGRAM_API_KEY")
    if not api_key:
        print("Missing IDEOGRAM_API_KEY")
        return
    
    response = requests.post(
        "https://api.ideogram.ai/v1/ideogram-v3/generate",
        headers={"Api-Key": api_key},
        json={
            "prompt": "A beautiful sunset over mountains",
            "rendering_speed": "TURBO"
        }
    )
    
    print(f"Ideogram Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Image URL: {result['data'][0]['url']}")
    else:
        print(f"Error: {response.text}")

async def test_veo3():
    """Test Veo 3 API directly"""
    try:
        from google import genai
        
        client = genai.Client()
        
        # First, test if client initializes
        print("Genai client initialized")
        
        # Try generating without an image first (simpler test)
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt="A cat walking in a garden"
        )
        
        print(f"Video generation started: {operation}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Try: pip install google-genai")
    except Exception as e:
        print(f"Veo 3 error: {e}")
        print(f"Error type: {type(e).__name__}")

async def test_storage():
    """Test Google Cloud Storage access"""
    try:
        from google.cloud import storage
        
        client = storage.Client()
        bucket_name = "agent-bake-off-episode-2.firebasestorage.app"
        bucket = client.bucket(bucket_name)
        
        # Test write access
        blob = bucket.blob("test/test.txt")
        blob.upload_from_string("test content")
        print(f"Storage write successful")
        
        # Test public access
        blob.make_public()
        print(f"Public URL: {blob.public_url}")
        
    except Exception as e:
        print(f"Storage error: {e}")

async def main():
    print("Testing Visual Generation Components\n")
    
    print("1. Testing Ideogram...")
    await test_ideogram()
    
    print("\n2. Testing Veo 3...")
    await test_veo3()
    
    print("\n3. Testing Storage...")
    await test_storage()

if __name__ == "__main__":
    asyncio.run(main())