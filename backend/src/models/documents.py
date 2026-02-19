"""
Document models for spec, plan, and task files.

Models:
- Document: Base document model
- Spec: Feature specification document
- Plan: Implementation plan document
- Task: Task breakdown document
- AnalysisResult: Task analysis results
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Document types in the feature workflow."""
    SPEC = "spec"
    PLAN = "plan"
    TASK = "task"
    CONSTITUTION = "constitution"  # Future feature


class DocumentStatus(str, Enum):
    """Document lifecycle status."""
    DRAFT = "draft"  # Initial creation
    IN_PROGRESS = "in_progress"  # Being edited
    READY_FOR_REVIEW = "ready_for_review"  # Complete, needs review
    APPROVED = "approved"  # Reviewed and approved
    ARCHIVED = "archived"  # No longer active


class Document(BaseModel):
    """
    Base document model.
    
    Represents any markdown document in the feature workflow.
    """
    document_id: str = Field(..., description="Unique document identifier")
    document_type: DocumentType = Field(..., description="Type of document")
    
    # Location
    feature_id: str = Field(..., description="Associated feature ID")
    file_path: str = Field(..., description="Path to document in repository")
    
    # Content
    content: str = Field(..., description="Document markdown content")
    content_hash: str = Field(..., description="SHA256 hash of content")
    
    # Metadata
    title: Optional[str] = Field(None, description="Document title (from first heading)")
    status: DocumentStatus = Field(default=DocumentStatus.DRAFT, description="Document status")
    
    # Version control
    version: int = Field(default=1, description="Document version number")
    github_sha: Optional[str] = Field(None, description="GitHub file SHA (for optimistic locking)")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Author
    last_modified_by_user_id: int = Field(..., description="User who last modified document")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_spec_abc123",
                "document_type": "spec",
                "feature_id": "feat_xyz789",
                "file_path": "specs/009-redesigned-workflow-ux/spec.md",
                "content": "# Feature Specification\n\n## Overview\n...",
                "content_hash": "abc123def456",
                "title": "Feature Specification",
                "status": "draft",
                "version": 1,
                "github_sha": "file_sha_abc123",
                "created_at": "2026-02-18T09:00:00Z",
                "updated_at": "2026-02-18T10:00:00Z",
                "last_modified_by_user_id": 12345678
            }
        }


class Spec(Document):
    """
    Feature specification document.
    
    Extends Document with spec-specific metadata.
    """
    document_type: DocumentType = Field(default=DocumentType.SPEC, description="Always 'spec'")
    
    # Spec-specific metadata
    user_stories: List[str] = Field(default_factory=list, description="Extracted user story IDs")
    requirements_count: Optional[int] = Field(None, description="Number of requirements")
    has_clarifications: bool = Field(default=False, description="Whether spec has clarifications")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_spec_abc123",
                "document_type": "spec",
                "feature_id": "feat_xyz789",
                "file_path": "specs/009-redesigned-workflow-ux/spec.md",
                "content": "# Feature Specification\n\n## User Stories\n- US0: Authentication\n- US1: Repository Selection\n...",
                "user_stories": ["US0", "US1", "US2"],
                "requirements_count": 15,
                "has_clarifications": True
            }
        }


class Plan(Document):
    """
    Implementation plan document.
    
    Extends Document with plan-specific metadata.
    """
    document_type: DocumentType = Field(default=DocumentType.PLAN, description="Always 'plan'")
    
    # Plan-specific metadata
    tech_stack: List[str] = Field(default_factory=list, description="Technologies/frameworks used")
    estimated_effort_weeks: Optional[int] = Field(None, description="Estimated implementation time")
    architecture_diagrams: List[str] = Field(default_factory=list, description="Diagram URLs/paths")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_plan_abc123",
                "document_type": "plan",
                "feature_id": "feat_xyz789",
                "file_path": "specs/009-redesigned-workflow-ux/plan.md",
                "content": "# Implementation Plan\n\n## Tech Stack\n- FastAPI\n- Next.js\n...",
                "tech_stack": ["FastAPI", "Next.js", "PostgreSQL"],
                "estimated_effort_weeks": 6,
                "architecture_diagrams": ["diagrams/architecture.png"]
            }
        }


class TaskItem(BaseModel):
    """Individual task item."""
    task_id: str = Field(..., description="Task identifier (e.g., T001)")
    title: str = Field(..., description="Task title/description")
    completed: bool = Field(default=False, description="Whether task is complete")
    parallelizable: bool = Field(default=False, description="Whether task can run in parallel")
    user_story: Optional[str] = Field(None, description="Associated user story (e.g., US0)")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this depends on")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "T001",
                "title": "Initialize Python backend project structure",
                "completed": True,
                "parallelizable": False,
                "user_story": None,
                "dependencies": []
            }
        }


class Task(Document):
    """
    Task breakdown document.
    
    Extends Document with task-specific metadata.
    """
    document_type: DocumentType = Field(default=DocumentType.TASK, description="Always 'task'")
    
    # Task-specific metadata
    total_tasks: int = Field(default=0, description="Total number of tasks")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    tasks: List[TaskItem] = Field(default_factory=list, description="Parsed task items")
    
    @property
    def completion_percentage(self) -> int:
        """Calculate completion percentage."""
        if self.total_tasks == 0:
            return 0
        return int((self.completed_tasks / self.total_tasks) * 100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_task_abc123",
                "document_type": "task",
                "feature_id": "feat_xyz789",
                "file_path": "specs/009-redesigned-workflow-ux/tasks.md",
                "content": "# Tasks\n\n- [x] T001: Initialize backend\n- [ ] T002: Setup frontend\n...",
                "total_tasks": 87,
                "completed_tasks": 20,
                "tasks": [
                    {
                        "task_id": "T001",
                        "title": "Initialize backend",
                        "completed": True,
                        "parallelizable": False
                    }
                ]
            }
        }


class AnalysisRisk(str, Enum):
    """Risk levels from analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisResult(BaseModel):
    """
    Task analysis results from Copilot CLI analyze operation.
    
    Represents AI-generated analysis of task completeness and risks.
    """
    analysis_id: str = Field(..., description="Unique analysis identifier")
    feature_id: str = Field(..., description="Associated feature ID")
    task_document_id: str = Field(..., description="Analyzed task document ID")
    
    # Analysis scores
    completeness_score: int = Field(..., ge=0, le=100, description="Task completeness score (0-100)")
    clarity_score: int = Field(..., ge=0, le=100, description="Task clarity score (0-100)")
    feasibility_score: int = Field(..., ge=0, le=100, description="Implementation feasibility (0-100)")
    
    # Identified risks
    risks: List[Dict[str, Any]] = Field(default_factory=list, description="Identified risks")
    # Each risk: {"level": "high/medium/low", "description": "...", "mitigation": "..."}
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # Missing items
    missing_tasks: List[str] = Field(default_factory=list, description="Potentially missing tasks")
    
    # Timestamps
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    analyzed_by_user_id: int = Field(..., description="User who requested analysis")
    
    # AI metadata
    ai_model: str = Field(default="github-copilot", description="AI model used for analysis")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="AI confidence level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "analysis_abc123",
                "feature_id": "feat_xyz789",
                "task_document_id": "doc_task_abc123",
                "completeness_score": 85,
                "clarity_score": 90,
                "feasibility_score": 80,
                "risks": [
                    {
                        "level": "medium",
                        "description": "WebSocket implementation may require additional error handling",
                        "mitigation": "Add comprehensive reconnection logic and message queuing"
                    }
                ],
                "recommendations": [
                    "Consider adding integration tests for WebSocket reconnection",
                    "Document API rate limiting strategy"
                ],
                "missing_tasks": [
                    "Database migration scripts (for Phase 2)",
                    "Performance benchmarking tasks"
                ],
                "analyzed_at": "2026-02-18T10:30:00Z",
                "analyzed_by_user_id": 12345678,
                "ai_model": "github-copilot",
                "confidence_score": 92
            }
        }


# ============================================================================
# Request/Response Models for Document Operations
# ============================================================================

class GetDocumentRequest(BaseModel):
    """Request model for fetching a document."""
    feature_id: str = Field(..., description="Feature ID")
    document_type: DocumentType = Field(..., description="Type of document to fetch")


class GetDocumentResponse(BaseModel):
    """Response model for document fetch."""
    document: Document = Field(..., description="Document content and metadata")


class UpdateDocumentRequest(BaseModel):
    """Request model for updating a document."""
    content: str = Field(..., description="Updated document content")
    if_match: Optional[str] = Field(None, description="Expected GitHub SHA for optimistic locking")


class UpdateDocumentResponse(BaseModel):
    """Response model for document update."""
    document: Document = Field(..., description="Updated document")
    message: str = Field(default="Document updated successfully", description="Success message")


class CreateDocumentRequest(BaseModel):
    """Request model for creating a new document."""
    feature_id: str = Field(..., description="Feature ID")
    document_type: DocumentType = Field(..., description="Type of document to create")
    content: Optional[str] = Field(None, description="Initial content (uses template if None)")


class CreateDocumentResponse(BaseModel):
    """Response model for document creation."""
    document: Document = Field(..., description="Created document")
    message: str = Field(default="Document created successfully", description="Success message")
