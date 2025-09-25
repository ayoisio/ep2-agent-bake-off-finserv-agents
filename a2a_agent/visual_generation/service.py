import os
import requests
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import asyncio
from google import genai
from google.cloud import storage
from google.cloud import firestore

class VisualGenerationService:
    def __init__(self):
        self.ideogram_api_key = os.environ.get("IDEOGRAM_API_KEY")
        self.genai_client = genai.Client()
        self.storage_client = storage.Client()
        self.db = firestore.Client()
        self.bucket_name = "agent-bake-off-episode-2.firebasestorage.app"
    
    async def generate_trip_visual(
        self,
        user_id: str,
        trip_id: str,
        prompt: str,
        reference_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Generate a trip visualization"""
        
        # Check if we already have this visual
        visual_ref = self.db.collection('trip_visuals').document(f"{trip_id}_{user_id}")
        existing = visual_ref.get()
        
        if existing.exists and not existing.to_dict().get('regenerate_requested'):
            return existing.to_dict()
        
        # Generate with Ideogram
        headers = {"Api-Key": self.ideogram_api_key}
        
        if reference_image:
            files = [("character_reference_images", ("image.png", reference_image))]
            data = {
                "style_type": "AUTO",
                "prompt": prompt,
                "rendering_speed": "TURBO"
            }
            response = requests.post(
                "https://api.ideogram.ai/v1/ideogram-v3/generate",
                headers=headers,
                data=data,
                files=files
            )
        else:
            response = requests.post(
                "https://api.ideogram.ai/v1/ideogram-v3/generate",
                headers=headers,
                json={"prompt": prompt, "rendering_speed": "TURBO"}
            )
        
        if response.status_code != 200:
            raise Exception(f"Ideogram API error: {response.status_code}")
        
        result = response.json()
        image_url = result['data'][0]['url']
        image_data = requests.get(image_url).content
        
        # Store image in GCS
        image_path = f"trips/{trip_id}/visuals/{user_id}_{uuid.uuid4()}.png"
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(image_path)
        blob.upload_from_string(image_data, content_type='image/png')
        blob.make_public()
        
        # Save metadata
        visual_data = {
            'user_id': user_id,
            'trip_id': trip_id,
            'prompt': prompt,
            'image_url': blob.public_url,
            'video_status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        visual_ref.set(visual_data)
        
        # Start video generation in background
        asyncio.create_task(self._generate_video_async(
            visual_ref.id, prompt, image_data
        ))
        
        return visual_data
    
    async def _generate_video_async(self, doc_id: str, prompt: str, image_data: bytes):
        """Generate video in background"""
        try:
            operation = self.genai_client.models.generate_videos(
                model="veo-3.0-generate-preview",
                prompt=prompt,
                image=image_data
            )
            
            # Poll for completion - Veo 3 can take several minutes
            max_attempts = 60  # Wait up to 10 minutes
            attempt = 0
            
            while not operation.done and attempt < max_attempts:
                await asyncio.sleep(10)
                # Refresh the operation status
                operation = self.genai_client.operations.get(operation.name)
                attempt += 1
            
            if not operation.done:
                raise Exception("Video generation timed out after 10 minutes")
            
            if operation.error:
                raise Exception(f"Video generation failed: {operation.error}")
            
            # Get the video data
            video = operation.result.generated_videos[0]
            video_data = video.video.read() if hasattr(video.video, 'read') else video.video
            
            # Store video
            video_path = f"trips/videos/{doc_id}.mp4"
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(video_path)
            blob.upload_from_string(video_data, content_type='video/mp4')
            blob.make_public()
            
            # Update document
            self.db.collection('trip_visuals').document(doc_id).update({
                'video_url': blob.public_url,
                'video_status': 'ready'
            })
        except Exception as e:
            self.db.collection('trip_visuals').document(doc_id).update({
                'video_status': 'failed',
                'video_error': str(e)
            })
