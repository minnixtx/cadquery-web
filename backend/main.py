from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional
import os

import base64

from backend.llm_client import LLMClient
from backend.executor import CadExecutor, extract_code, SYSTEM_PROMPT, ERROR_RECOVERY_PROMPT, SELF_ASSESS_PROMPT
from backend.exporter import ModelExporter
from backend.screenshot import screenshotter

app = FastAPI(title="NL 3D Modeler")

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


class Settings(BaseModel):
    endpoint: str = "http://localhost:8000/v1"
    model: str = "llama"
    api_key: Optional[str] = None


settings = Settings(
    endpoint=os.environ.get("LLM_ENDPOINT", "http://localhost:8000/v1"),
    model=os.environ.get("LLM_MODEL", "llama"),
    api_key=os.environ.get("LLM_API_KEY") or None,
)


class ChatRequest(BaseModel):
    message: str


class ExportRequest(BaseModel):
    fmt: str = "stl"


# In-memory session state
conversation_history: list[str] = []
current_script: str = ""
current_tjs_base64: str = ""
executor = CadExecutor()


def get_llm_client() -> LLMClient:
    return LLMClient(
        base_url=settings.endpoint,
        model=settings.model,
        api_key=settings.api_key,
    )


@app.get("/api/settings")
def get_settings():
    return settings.model_dump()


@app.put("/api/settings")
def update_settings(new: Settings):
    global settings
    settings = new
    return {"status": "ok"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Process a natural language message, generate CADQuery code, execute it.

    Returns the CADQuery script, TJS data for the viewer, and chat response.
    """
    global conversation_history, current_script, current_tjs_base64

    client = get_llm_client()
    user_message = req.message

    # Build conversation context
    messages = [SYSTEM_PROMPT]
    messages.extend(conversation_history)
    messages.append(f"User request: {user_message}")

    if current_script:
        messages.append(f"Current CADQuery script:\n{current_script}")

    # Send to LLM
    try:
        llm_response = client.chat(messages)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    # Extract code from response
    code = extract_code(llm_response)

    # Execute the script
    error, success_msg = executor.execute(code)

    if error:
        # Auto-retry: send error back to LLM
        retry_prompt = ERROR_RECOVERY_PROMPT.format(
            error=error, user_request=user_message
        )
        try:
            retry_response = client.chat([SYSTEM_PROMPT, retry_prompt])
            code = extract_code(retry_response)
            error, success_msg = executor.execute(code)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM retry error: {e}")

    if error:
        raise HTTPException(status_code=500, detail=f"CADQuery error (retry failed): {error}")

    # Export TJS
    try:
        tjs_b64 = ModelExporter.to_tjs_base64(executor.result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")

    # Visual self-assessment loop
    for _ in range(2):
        try:
            tjs_text = base64.b64decode(tjs_b64).decode("utf-8")
            screenshot_b64 = screenshotter.capture(tjs_text)
        except Exception:
            break

        assess_prompt = SELF_ASSESS_PROMPT.format(user_request=user_message)
        try:
            assess_response = client.chat([assess_prompt], images=[screenshot_b64])
        except Exception:
            break

        if "APPROVED" in assess_response.upper():
            break

        # LLM provided a fix — re-execute
        fix_code = extract_code(assess_response)
        if fix_code == assess_response.strip():
            break
        error, _ = executor.execute(fix_code)
        if error:
            break
        try:
            tjs_b64 = ModelExporter.to_tjs_base64(executor.result)
        except Exception:
            break
        code = fix_code

    # Update state
    conversation_history.append(f"User: {user_message}")
    conversation_history.append(f"Model produced script.")
    # Keep history bounded
    if len(conversation_history) > 20:
        conversation_history = conversation_history[-16:]
    current_script = code
    current_tjs_base64 = tjs_b64

    return {
        "code": code,
        "tjs": tjs_b64,
        "response": success_msg,
    }


@app.get("/api/model")
def get_model():
    """Return the current TJS data for the 3D viewer."""
    return {"tjs": current_tjs_base64, "code": current_script}


@app.post("/api/export")
def export_model(req: ExportRequest):
    """Export the current model as STL or STEP."""
    if executor.result is None:
        raise HTTPException(status_code=400, detail="No model to export. Create one first.")

    fmt = req.fmt.lower()
    if fmt == "stl":
        data = ModelExporter.to_stl(executor.result)
        media_type = "application/sla"
    elif fmt == "step":
        data = ModelExporter.to_step(executor.result)
        media_type = "model/step"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}. Use 'stl' or 'step'.")

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="model.{fmt}"'},
    )


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")
