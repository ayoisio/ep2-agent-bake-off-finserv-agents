import os
import time
import base64
import requests
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types

class TravelVisualizationTools:
    def __init__(self):
        self.ideogram_api_key = os.getenv("IDEOGRAM_API_KEY")
        self.genai_client = genai.Client()
        
    def generate_travel_portrait(self, 
                                destination: str,
                                character_image_path: str,
                                scene_description: Optional[str] = None) -> Dict[str, Any]:
        """Generate a travel portrait using Ideogram's character reference API"""
        
        # Default prompts for popular destinations
        destination_prompts = {
            "paris": "A cinematic medium shot of a person sitting at a charming Parisian cafe, wearing a stylish beret, with the Eiffel Tower visible in the background, golden hour lighting",
            "tokyo": "A vibrant street scene in Tokyo at night, person standing in front of neon signs in Shibuya, wearing modern streetwear",
            "bali": "A serene shot of a person meditating on a beautiful Bali beach at sunset, wearing comfortable resort wear",
            "rome": "A classic portrait of a person tossing a coin into the Trevi Fountain, wearing elegant Italian fashion",
            "dubai": "A luxurious shot of a person on a rooftop terrace overlooking Dubai skyline, dressed in sophisticated evening wear",
            "default": f"A beautiful travel portrait of a person enjoying their vacation in {destination}, professional photography"
        }
        
        # Use custom scene or default based on destination
        prompt = scene_description or destination_prompts.get(
            destination.lower(), 
            destination_prompts["default"]
        )
        
        try:
            # Call Ideogram API with character reference
            with open(character_image_path, 'rb') as f:
                response = requests.post(
                    "https://api.ideogram.ai/v1/ideogram-v3/generate",
                    headers={"Api-Key": self.ideogram_api_key},
                    data={
                        "style_type": "PHOTO",
                        "prompt": prompt,
                        "rendering_speed": "TURBO"
                    },
                    files=[("character_reference_images", f)]
                )
            
            if response.status_code == 200:
                result = response.json()
                image_url = result['data'][0]['url']
                
                # Download and save the image
                image_response = requests.get(image_url)
                output_path = f"temp_travel_portrait_{int(time.time())}.png"
                with open(output_path, 'wb') as f:
                    f.write(image_response.content)
                
                return {
                    "success": True,
                    "image_path": output_path,
                    "image_url": image_url,
                    "prompt_used": prompt
                }
            else:
                return {
                    "success": False,
                    "error": f"Ideogram API error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_travel_video(self, 
                             image_path: str,
                             destination: str,
                             video_style: str = "cinematic") -> Dict[str, Any]:
        """Generate a travel video using Veo 3 from the portrait"""
        
        video_prompts = {
            "cinematic": f"A cinematic camera movement showcasing the person exploring {destination}, smooth dolly shots, professional cinematography",
            "energetic": f"Dynamic fast-paced montage of adventures in {destination}, quick cuts, upbeat energy",
            "peaceful": f"Slow, peaceful scenes of relaxation and tranquility in {destination}, gentle camera movements",
            "luxury": f"Luxurious travel experience in {destination}, elegant camera work, high-end atmosphere"
        }
        
        prompt = video_prompts.get(video_style, video_prompts["cinematic"])
        
        try:
            # Read the image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Create image object for Veo
            image = types.Image(data=image_data)
            
            # Generate video with Veo 3
            operation = self.genai_client.models.generate_videos(
                model="veo-3.0-generate-preview",
                prompt=prompt,
                image=image,
            )
            
            # Poll until complete
            while not operation.done:
                time.sleep(10)
                operation = self.genai_client.operations.get(operation)
            
            # Save the video
            video = operation.response.generated_videos[0]
            output_path = f"travel_video_{destination}_{int(time.time())}.mp4"
            self.genai_client.files.download(file=video.video)
            video.video.save(output_path)
            
            return {
                "success": True,
                "video_path": output_path,
                "prompt_used": prompt
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_savings_timeline(self, 
                                  destination: str,
                                  monthly_savings: float) -> Dict[str, Any]:
        """Calculate how long it will take to save for the trip"""
        
        # Rough trip costs (could be enhanced with real data)
        estimated_costs = {
            "paris": 3000,
            "tokyo": 3500,
            "bali": 2000,
            "rome": 2500,
            "dubai": 4000,
            "default": 2500
        }
        
        trip_cost = estimated_costs.get(destination.lower(), estimated_costs["default"])
        months_to_save = trip_cost / monthly_savings if monthly_savings > 0 else 0
        
        return {
            "destination": destination,
            "estimated_cost": trip_cost,
            "monthly_savings": monthly_savings,
            "months_to_save": round(months_to_save, 1),
            "savings_tips": [
                f"Save ${monthly_savings}/month to reach your goal in {round(months_to_save, 1)} months",
                f"Increase savings to ${monthly_savings * 1.5}/month to get there in {round(months_to_save/1.5, 1)} months",
                "Consider travel rewards credit cards for additional savings",
                "Book flights 2-3 months in advance for best prices"
            ]
        }
