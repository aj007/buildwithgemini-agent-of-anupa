"""Image generation tool for TriCoach AI using gemini-3.1-flash-lite-image model.

Key requirements:
1. Model: gemini-3.1-flash-lite-image in global region
2. Save artifact using tool_context.save_artifact
3. Upload image bytes to public Cloud Storage bucket "tricoach-assets-44253ac8b396"
4. Return public HTTPS URL (https://storage.googleapis.com/<bucket>/<object>)
5. No local file write.
"""

import uuid
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

BUCKET_NAME = "tricoach-assets-44253ac8b396"
GCP_PROJECT_ID = "qwiklabs-gcp-01-44253ac8b396"


def generate_workout_badge(prompt: str, tool_context: ToolContext) -> str:
    """Generates a custom triathlon or fitness milestone badge/artwork using Gemini image generation,
    saves it as an artifact in the playground, and uploads it to a public Cloud Storage bucket.

    Args:
        prompt: Detailed description of the image/badge to generate (e.g., 'A golden 45-Min Tempo Run finisher badge').
        tool_context: ADK ToolContext automatically injected by the runtime.

    Returns:
        The public HTTPS URL of the uploaded image asset.
    """
    try:
        client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=f"High quality digital fitness badge: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        image_bytes = None
        if response.parts:
            for part in response.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    break

        if not image_bytes:
            return "Failed to generate image bytes from model."

        filename = f"badge_{uuid.uuid4().hex[:8]}.png"

        # 1. Save artifact in Playground
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes directly to public GCS bucket (no local file write)
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"badges/{filename}")
        blob.upload_from_string(image_bytes, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/badges/{filename}"
        return (
            f"Successfully generated image and uploaded to Cloud Storage!\n"
            f"- Public URL: {public_url}\n"
            f"- Artifact Saved: {filename}"
        )
    except Exception as e:
        return f"Error generating or uploading image: {str(e)}"
