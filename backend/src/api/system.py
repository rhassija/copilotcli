"""
System diagnostic endpoints.

Provides:
- Copilot CLI status check
- System health information
"""

from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
import logging

router = APIRouter(prefix="/api/v1/system", tags=["system"])
logger = logging.getLogger(__name__)


class CopilotStatusResponse(BaseModel):
    """Response model for Copilot CLI status."""
    available: bool
    path: str
    message: str


@router.get("/copilot-status", response_model=CopilotStatusResponse)
async def get_copilot_status():
    """
    Check if Copilot CLI is available on the system.
    
    Mirrors the check from app.py sidebar (lines 433-440).
    
    Returns:
        CopilotStatusResponse with availability status and details
    """
    # Same path as POC app.py
    copilot_path = Path.home() / "Library/Application Support/Code/User/globalStorage/github.copilot-chat/copilotCli/copilot"
    
    available = copilot_path.exists()
    
    if available:
        message = "Copilot CLI is available and ready to use"
        logger.info(f"Copilot CLI found at: {copilot_path}")
    else:
        message = "Copilot CLI not found. Install GitHub Copilot extension in VS Code."
        logger.warning(f"Copilot CLI not found at: {copilot_path}")
    
    return CopilotStatusResponse(
        available=available,
        path=str(copilot_path),
        message=message
    )
