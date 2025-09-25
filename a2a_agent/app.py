import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import base64
import uuid
from datetime import datetime

# Your imports
from gemini_agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.genai.types import Content, Part

# Visual generation imports
import requests
import hashlib
import asyncio
from google import genai
from google.cloud import storage
from google.cloud import firestore

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cymbal Bank AI Agent API",
    description="Financial Assistant powered by Gemini",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ADK services
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
memory_service = InMemoryMemoryService()

# Create runner
runner = Runner(
    app_name="cymbal_bank_ai_agent",
    agent=root_agent,
    session_service=session_service,
    artifact_service=artifact_service,
    memory_service=memory_service,
)

# Initialize Visual Generation Service
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
        blob.upload_from_string(image_data)
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
            
            while not operation.done:
                await asyncio.sleep(10)
                operation = self.genai_client.operations.get(operation)
            
            video = operation.response.generated_videos[0]
            
            # Store video
            video_path = f"trips/videos/{doc_id}.mp4"
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(video_path)
            blob.upload_from_string(video.video.read())
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

# Initialize visual service
visual_service = VisualGenerationService()

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: str = "user-001"
    session_id: Optional[str] = None
    skill: str = "chat"  # "chat" or "backend_services"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    skill_used: str
    artifacts: Optional[List[Dict[str, Any]]] = None  # For graphs/images

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cymbal-bank-ai-agent",
        "version": "1.0.0"
    }

@app.get("/debug/artifacts/{user_id}/{session_id}")
async def debug_artifacts(user_id: str, session_id: str):
    """Debug endpoint to check what artifacts exist for a session"""
    try:
        artifacts = await artifact_service.list_artifact_keys(
            app_name="cymbal_bank_ai_agent",
            user_id=user_id,
            session_id=session_id,
        )
        return {
            "artifacts": artifacts,
            "count": len(artifacts)
        }
    except Exception as e:
        return {
            "error": str(e),
            "artifacts": [],
            "count": 0
        }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate session ID if not provided
        if not request.session_id:
            import uuid
            request.session_id = str(uuid.uuid4())
        
        logger.info(f"Processing {request.skill} request for user {request.user_id}, session: {request.session_id}")
        logger.info(f"Request message: {request.message[:100]}...")
        
        # Create or get session
        session = await runner.session_service.get_session(
            app_name="cymbal_bank_ai_agent",
            user_id=request.user_id,
            session_id=request.session_id,
        )
        
        if not session:
            session = await runner.session_service.create_session(
                app_name="cymbal_bank_ai_agent",
                user_id=request.user_id,
                session_id=request.session_id,
                state={"user_id": request.user_id}
            )
        
        # Create user message
        user_content = Content(role="user", parts=[Part(text=request.message)])
        
        # Process through runner
        response_text = ""
        artifacts = []
        
        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=user_content,
        ):
            # Check for artifacts in event actions
            if hasattr(event, 'actions') and event.actions and hasattr(event.actions, 'artifact_delta') and event.actions.artifact_delta:
                logger.info(f"Found artifact_delta: {event.actions.artifact_delta}")
                for artifact_name, version in event.actions.artifact_delta.items():
                    if artifact_name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        logger.info(f"Loading artifact: {artifact_name}")
                        # Load the artifact
                        artifact = await artifact_service.load_artifact(
                            app_name="cymbal_bank_ai_agent",
                            user_id=request.user_id,
                            session_id=request.session_id,
                            filename=artifact_name
                        )
                        if artifact and hasattr(artifact, 'inline_data'):
                            # Convert to base64 for frontend
                            image_base64 = base64.b64encode(artifact.inline_data.data).decode('utf-8')
                            artifacts.append({
                                "type": "image",
                                "name": artifact_name,
                                "data": f"data:image/png;base64,{image_base64}",
                                "mime_type": "image/png"
                            })
                            logger.info(f"Successfully loaded artifact: {artifact_name}")
                        else:
                            logger.warning(f"Could not load artifact: {artifact_name}")
            
            # Check for artifacts (graphs/images) in event.artifacts
            if hasattr(event, 'artifacts') and event.artifacts:
                logger.info(f"Found event.artifacts: {event.artifacts}")
                for artifact_name, artifact_data in event.artifacts.items():
                    if artifact_name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        # Load the artifact
                        artifact = await artifact_service.load_artifact(
                            app_name="cymbal_bank_ai_agent",
                            user_id=request.user_id,
                            session_id=request.session_id,
                            filename=artifact_name
                        )
                        if artifact and hasattr(artifact, 'inline_data'):
                            # Convert to base64 for frontend
                            image_base64 = base64.b64encode(artifact.inline_data.data).decode('utf-8')
                            artifacts.append({
                                "type": "image",
                                "name": artifact_name,
                                "data": f"data:image/png;base64,{image_base64}",
                                "mime_type": "image/png"
                            })
            
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                
                # Check for artifacts in final session after completion
                session = await runner.session_service.get_session(
                    app_name="cymbal_bank_ai_agent",
                    user_id=request.user_id,
                    session_id=request.session_id,
                )
                
                # List all artifacts for this session
                try:
                    available_artifacts = await artifact_service.list_artifact_keys(
                        app_name="cymbal_bank_ai_agent",
                        user_id=request.user_id,
                        session_id=request.session_id,
                    )
                    logger.info(f"Available artifacts: {available_artifacts}")
                    
                    for artifact_name in available_artifacts:
                        if artifact_name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            # Check if we haven't already added this artifact
                            if not any(a['name'] == artifact_name for a in artifacts):
                                artifact = await artifact_service.load_artifact(
                                    app_name="cymbal_bank_ai_agent",
                                    user_id=request.user_id,
                                    session_id=request.session_id,
                                    filename=artifact_name
                                )
                                if artifact and hasattr(artifact, 'inline_data'):
                                    image_base64 = base64.b64encode(artifact.inline_data.data).decode('utf-8')
                                    artifacts.append({
                                        "type": "image",
                                        "name": artifact_name,
                                        "data": f"data:image/png;base64,{image_base64}",
                                        "mime_type": "image/png"
                                    })
                                    logger.info(f"Added artifact from session: {artifact_name}")
                except Exception as e:
                    logger.error(f"Error listing artifacts: {e}")
                
                break
        
        logger.info(f"Final response - Found {len(artifacts)} artifacts")
        if artifacts:
            logger.info(f"Artifact names: {[a['name'] for a in artifacts]}")
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            skill_used=request.skill,
            artifacts=artifacts if artifacts else None
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Visual Generation Endpoints
@app.post("/api/trips/{trip_id}/visualize")
async def generate_trip_visual(
    trip_id: str,
    prompt: str = Form(...),
    user_id: str = Form(...),
    reference_image: Optional[UploadFile] = File(None)
):
    """Generate visual for a trip"""
    try:
        image_data = None
        if reference_image:
            image_data = await reference_image.read()
        
        result = await visual_service.generate_trip_visual(
            user_id=user_id,
            trip_id=trip_id,
            prompt=prompt,
            reference_image=image_data
        )
        
        return result
    except Exception as e:
        logger.error(f"Error generating visual: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trips/{trip_id}/visuals")
async def get_trip_visuals(trip_id: str):
    """Get all visuals for a trip"""
    try:
        visuals = visual_service.db.collection('trip_visuals')\
            .where('trip_id', '==', trip_id)\
            .stream()
        
        return [v.to_dict() for v in visuals]
    except Exception as e:
        logger.error(f"Error fetching visuals: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trips/{trip_id}/invite")
async def invite_to_trip(
    trip_id: str, 
    email: str = Form(...), 
    inviter_id: str = Form(...)
):
    """Send trip invitation"""
    try:
        # Create invitation record
        invitation = {
            'trip_id': trip_id,
            'inviter_id': inviter_id,
            'invitee_email': email,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'invitation_id': str(uuid.uuid4())
        }
        
        visual_service.db.collection('trip_invitations').add(invitation)
        
        # Could send email here using SendGrid or similar
        
        return {"status": "invitation_sent", "invitation": invitation}
    except Exception as e:
        logger.error(f"Error sending invitation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trips/{trip_id}/members")
async def get_trip_members(trip_id: str):
    """Get all members of a trip"""
    try:
        # Get accepted invitations
        invitations = visual_service.db.collection('trip_invitations')\
            .where('trip_id', '==', trip_id)\
            .where('status', '==', 'accepted')\
            .stream()
        
        members = []
        for inv in invitations:
            inv_data = inv.to_dict()
            members.append({
                'email': inv_data.get('invitee_email'),
                'joined_at': inv_data.get('accepted_at', inv_data.get('created_at'))
            })
        
        return members
    except Exception as e:
        logger.error(f"Error fetching trip members: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/invitations/{invitation_id}/accept")
async def accept_invitation(invitation_id: str, user_id: str = Form(...)):
    """Accept a trip invitation"""
    try:
        # Update invitation status
        invitations = visual_service.db.collection('trip_invitations')\
            .where('invitation_id', '==', invitation_id)\
            .limit(1)\
            .stream()
        
        for inv in invitations:
            inv.reference.update({
                'status': 'accepted',
                'accepted_by': user_id,
                'accepted_at': datetime.utcnow().isoformat()
            })
            return {"status": "accepted", "trip_id": inv.to_dict().get('trip_id')}
        
        raise HTTPException(status_code=404, detail="Invitation not found")
    except Exception as e:
        logger.error(f"Error accepting invitation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Cymbal Bank AI Agent API",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "docs": "/docs",
            "visual_generation": {
                "generate": "/api/trips/{trip_id}/visualize",
                "get_visuals": "/api/trips/{trip_id}/visuals",
                "invite": "/api/trips/{trip_id}/invite",
                "members": "/api/trips/{trip_id}/members",
                "accept_invitation": "/api/invitations/{invitation_id}/accept"
            }
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
