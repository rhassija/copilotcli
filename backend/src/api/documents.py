"""
Document API endpoints for spec/plan/task management.

Provides:
- Fetch spec/plan/task documents from feature branches
- Update and save documents to GitHub
- Document versioning with SHA-based optimistic locking
- Template generation for new documents
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header, Body
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import asyncio
import logging

from src.models.github import Feature
from src.models.websocket import WebSocketMessage, MessageType, MessagePriority
from src.services.github_client import GitHubClient, GitHubAPIError
from src.services.auth_service import auth_service
from src.services.storage import storage
from src.services.document_generator import DocumentGenerator
from src.services.websocket_manager import connection_manager
from src.utils.error_handlers import create_error_response
import uuid

router = APIRouter(prefix="/api/v1/features", tags=["documents"])
logger = logging.getLogger(__name__)


# ========================================================================
# Dependency: Get GitHub Client from Session
# ========================================================================

async def get_github_client(
    x_session_id: str = Header(..., description="Session ID")
) -> GitHubClient:
    """
    Get authenticated GitHub client from session.
    
    Args:
        x_session_id: Session ID from X-Session-ID header
    
    Returns:
        GitHubClient instance with user's token
    
    Raises:
        HTTPException: If session invalid or token missing
    """
    token = auth_service.get_session_token(x_session_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return GitHubClient(token)


# ========================================================================
# Request/Response Models
# ========================================================================

class DocumentContent(BaseModel):
    """Document (spec, plan, or task) content."""
    content: str = Field(..., description="Document markdown content")
    sha: str = Field(..., description="File SHA for optimistic locking")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    path: str = Field(..., description="Path in repository")


class DocumentUpdateRequest(BaseModel):
    """Request to update a document."""
    content: str = Field(..., description="Updated document content (markdown)")
    sha: str = Field(..., description="Current file SHA (for optimistic locking)")
    message: Optional[str] = Field(
        None,
        description="Commit message (auto-generated if not provided)"
    )


class DocumentUpdateResponse(BaseModel):
    """Response from document update."""
    sha: str = Field(..., description="New file SHA")
    path: str = Field(..., description="Document path")
    updated_at: datetime = Field(..., description="Update timestamp")
    message: str = Field(default="Document updated successfully")


class DocumentResponse(BaseModel):
    """Response containing document content and metadata."""
    content: str = Field(..., description="Document markdown content")
    sha: str = Field(..., description="Current file SHA")
    path: str = Field(..., description="File path in repository")
    repository: str = Field(..., description="Repository full name")
    branch: str = Field(..., description="Branch name")
    last_modified: datetime = Field(..., description="Last modification timestamp")


class DocumentTemplate(BaseModel):
    """Template for a new document."""
    name: str = Field(..., description="Template name (spec, plan, task)")
    content: str = Field(..., description="Template markdown content")


# ========================================================================
# Document Type Constants
# ========================================================================

DOCUMENT_TEMPLATES = {
    "spec": """# Feature Specification

**Feature Branch**: {branch_name}
**Created**: {created_at}
**Status**: Draft

## Overview

{feature_title}

## Requirements

- Requirement 1
- Requirement 2
- Requirement 3

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Considerations

- Implementation approach
- Dependencies
- Performance requirements

## References

- Related issues
- Documentation links
""",
    "plan": """# Implementation Plan: {feature_title}

**Branch**: {branch_name} | **Created**: {created_at}

## Summary

Brief overview of the feature and implementation strategy.

## Technical Context

**Language/Version**: [Specify]
**Dependencies**: 
- Dependency 1
- Dependency 2

**Architecture**:
- Component 1
- Component 2

## Implementation Phases

### Phase 1: Setup
- [ ] Task 1
- [ ] Task 2

### Phase 2: Core Development
- [ ] Task 3
- [ ] Task 4

### Phase 3: Testing
- [ ] Task 5
- [ ] Task 6

### Phase 4: Integration
- [ ] Task 7
- [ ] Task 8

## Risks and Mitigation

- Risk 1: Mitigation
- Risk 2: Mitigation

## Rollout Plan

Initial deployment steps and rollback procedures.
""",
    "task": """# Task List: {feature_title}

**Branch**: {branch_name} | **Created**: {created_at}

## Tasks

### Setup Phase
- [ ] T001: Initialize project structure
- [ ] T002: Set up development environment
- [ ] T003: Create CI/CD pipeline

### Implementation Phase
- [ ] T004: Implement core functionality
- [ ] T005: Add configuration support
- [ ] T006: Implement error handling

### Testing Phase
- [ ] T007: Write unit tests
- [ ] T008: Write integration tests
- [ ] T009: Perform manual testing

### Integration Phase
- [ ] T010: Merge feature branch
- [ ] T011: Deploy to staging
- [ ] T012: Deploy to production

## Progress

- **Completed**: 0 / 12
- **In Progress**: 0
- **Blocked**: 0

## Notes

Add any additional notes or implementation details here.
"""
}

DOCUMENT_PATHS = {
    "spec": "specs/{branch}/spec.md",
    "plan": "specs/{branch}/plan.md",
    "task": "specs/{branch}/task.md"
}


# ========================================================================
# T108: Get Spec Document Endpoint
# ========================================================================

@router.get("/{feature_id}/spec", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_spec(
    feature_id: str,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Fetch spec.md document for a feature.
    
    Implements T108:
    - Retrieves spec document from feature branch
    - Returns content with SHA for optimistic locking
    - Returns file metadata
    
    Args:
        feature_id: Feature identifier
        github_client: Authenticated GitHub client
    
    Returns:
        DocumentResponse with spec content
    
    Raises:
        HTTPException: If feature not found or fetch fails
    """
    try:
        # Get feature from storage
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        # Determine spec path
        spec_path = feature.spec_path or DOCUMENT_PATHS["spec"].format(branch=feature.branch_name)
        
        # Fetch from GitHub
        content, sha = await github_client.read_file(
            repo_full_name=feature.repository_full_name,
            path=spec_path,
            branch=feature.branch_name,
            use_cache=True
        )
        
        logger.info(f"Retrieved spec for feature {feature_id}")
        
        return DocumentResponse(
            content=content,
            sha=sha,
            path=spec_path,
            repository=feature.repository_full_name,
            branch=feature.branch_name,
            last_modified=feature.updated_at
        )
        
    except GitHubAPIError as e:
        logger.error(f"GitHub API error fetching spec: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch spec: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error fetching spec: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch spec: {str(e)}"
        )


# ========================================================================
# T109: Update Spec Document Endpoint
# ========================================================================

@router.put("/{feature_id}/spec", response_model=DocumentUpdateResponse, status_code=status.HTTP_200_OK)
async def update_spec(
    feature_id: str,
    request: DocumentUpdateRequest,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Update and save spec.md document for a feature.
    
    Implements T109:
    - Saves spec document to feature branch
    - Uses optimistic locking with SHA verification
    - Updates feature metadata
    
    Args:
        feature_id: Feature identifier
        request: Update request with content and SHA
        github_client: Authenticated GitHub client
    
    Returns:
        DocumentUpdateResponse with new SHA
    
    Raises:
        HTTPException: If feature not found, SHA mismatch, or save fails
    """
    try:
        # Get feature from storage
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        # Determine spec path
        spec_path = feature.spec_path or DOCUMENT_PATHS["spec"].format(branch=feature.branch_name)
        
        # Generate commit message if not provided
        message = request.message or f"Update spec for feature: {feature.title}"
        
        # Write to GitHub with optimistic locking
        new_sha = await github_client.write_file(
            repo_full_name=feature.repository_full_name,
            path=spec_path,
            content=request.content,
            message=message,
            branch=feature.branch_name,
            sha=request.sha
        )
        
        # Update feature metadata
        feature.updated_at = datetime.utcnow()
        storage.save_feature(feature)
        
        logger.info(f"Updated spec for feature {feature_id}")
        
        return DocumentUpdateResponse(
            sha=new_sha,
            path=spec_path,
            updated_at=datetime.utcnow()
        )
        
    except GitHubAPIError as e:
        if "SHA mismatch" in str(e):
            logger.warning(f"Optimistic locking conflict for spec: {feature_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has been modified. Please refresh and try again."
            )
        logger.error(f"GitHub API error updating spec: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update spec: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error updating spec: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update spec: {str(e)}"
        )


# ========================================================================
# T110: Get Plan Document Endpoint
# ========================================================================

@router.get("/{feature_id}/plan", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_plan(
    feature_id: str,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Fetch plan.md document for a feature.
    
    Implements T110:
    - Retrieves plan document from feature branch
    - Returns content with SHA for optimistic locking
    - Returns file metadata
    
    Args:
        feature_id: Feature identifier
        github_client: Authenticated GitHub client
    
    Returns:
        DocumentResponse with plan content
    
    Raises:
        HTTPException: If feature not found or fetch fails
    """
    try:
        # Get feature from storage
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        # Determine plan path
        plan_path = feature.plan_path or DOCUMENT_PATHS["plan"].format(branch=feature.branch_name)
        
        # Fetch from GitHub
        content, sha = await github_client.read_file(
            repo_full_name=feature.repository_full_name,
            path=plan_path,
            branch=feature.branch_name,
            use_cache=True
        )
        
        logger.info(f"Retrieved plan for feature {feature_id}")
        
        return DocumentResponse(
            content=content,
            sha=sha,
            path=plan_path,
            repository=feature.repository_full_name,
            branch=feature.branch_name,
            last_modified=feature.updated_at
        )
        
    except GitHubAPIError as e:
        logger.error(f"GitHub API error fetching plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch plan: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error fetching plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch plan: {str(e)}"
        )


# ========================================================================
# T111: Update Plan Document Endpoint
# ========================================================================

@router.put("/{feature_id}/plan", response_model=DocumentUpdateResponse, status_code=status.HTTP_200_OK)
async def update_plan(
    feature_id: str,
    request: DocumentUpdateRequest,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Update and save plan.md document for a feature.
    
    Implements T111:
    - Saves plan document to feature branch
    - Uses optimistic locking with SHA verification
    - Updates feature metadata
    
    Args:
        feature_id: Feature identifier
        request: Update request with content and SHA
        github_client: Authenticated GitHub client
    
    Returns:
        DocumentUpdateResponse with new SHA
    
    Raises:
        HTTPException: If feature not found, SHA mismatch, or save fails
    """
    try:
        # Get feature from storage
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        # Determine plan path
        plan_path = feature.plan_path or DOCUMENT_PATHS["plan"].format(branch=feature.branch_name)
        
        # Generate commit message if not provided
        message = request.message or f"Update plan for feature: {feature.title}"
        
        # Write to GitHub with optimistic locking
        new_sha = await github_client.write_file(
            repo_full_name=feature.repository_full_name,
            path=plan_path,
            content=request.content,
            message=message,
            branch=feature.branch_name,
            sha=request.sha
        )
        
        # Update feature metadata
        feature.updated_at = datetime.utcnow()
        storage.save_feature(feature)
        
        logger.info(f"Updated plan for feature {feature_id}")
        
        return DocumentUpdateResponse(
            sha=new_sha,
            path=plan_path,
            updated_at=datetime.utcnow()
        )
        
    except GitHubAPIError as e:
        if "SHA mismatch" in str(e):
            logger.warning(f"Optimistic locking conflict for plan: {feature_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has been modified. Please refresh and try again."
            )
        logger.error(f"GitHub API error updating plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update plan: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error updating plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update plan: {str(e)}"
        )


# ========================================================================
# T112: Get Task Document Endpoint
# ========================================================================

@router.get("/{feature_id}/task", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_task(
    feature_id: str,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Fetch task.md document for a feature.
    
    Implements T112:
    - Retrieves task document from feature branch
    - Returns content with SHA for optimistic locking
    - Returns file metadata
    
    Args:
        feature_id: Feature identifier
        github_client: Authenticated GitHub client
    
    Returns:
        DocumentResponse with task content
    
    Raises:
        HTTPException: If feature not found or fetch fails
    """
    try:
        # Get feature from storage
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        # Determine task path
        task_path = feature.task_path or DOCUMENT_PATHS["task"].format(branch=feature.branch_name)
        
        # Fetch from GitHub
        content, sha = await github_client.read_file(
            repo_full_name=feature.repository_full_name,
            path=task_path,
            branch=feature.branch_name,
            use_cache=True
        )
        
        logger.info(f"Retrieved task for feature {feature_id}")
        
        return DocumentResponse(
            content=content,
            sha=sha,
            path=task_path,
            repository=feature.repository_full_name,
            branch=feature.branch_name,
            last_modified=feature.updated_at
        )
        
    except GitHubAPIError as e:
        logger.error(f"GitHub API error fetching task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch task: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error fetching task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task: {str(e)}"
        )


# ========================================================================
# T113: Update Task Document Endpoint
# ========================================================================

@router.put("/{feature_id}/task", response_model=DocumentUpdateResponse, status_code=status.HTTP_200_OK)
async def update_task(
    feature_id: str,
    request: DocumentUpdateRequest,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Update and save task.md document for a feature.
    
    Implements T113:
    - Saves task document to feature branch
    - Uses optimistic locking with SHA verification
    - Updates feature metadata
    
    Args:
        feature_id: Feature identifier
        request: Update request with content and SHA
        github_client: Authenticated GitHub client
    
    Returns:
        DocumentUpdateResponse with new SHA
    
    Raises:
        HTTPException: If feature not found, SHA mismatch, or save fails
    """
    try:
        # Get feature from storage
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        # Determine task path
        task_path = feature.task_path or DOCUMENT_PATHS["task"].format(branch=feature.branch_name)
        
        # Generate commit message if not provided
        message = request.message or f"Update task list for feature: {feature.title}"
        
        # Write to GitHub with optimistic locking
        new_sha = await github_client.write_file(
            repo_full_name=feature.repository_full_name,
            path=task_path,
            content=request.content,
            message=message,
            branch=feature.branch_name,
            sha=request.sha
        )
        
        # Update feature metadata
        feature.updated_at = datetime.utcnow()
        storage.save_feature(feature)
        
        logger.info(f"Updated task for feature {feature_id}")
        
        return DocumentUpdateResponse(
            sha=new_sha,
            path=task_path,
            updated_at=datetime.utcnow()
        )
        
    except GitHubAPIError as e:
        if "SHA mismatch" in str(e):
            logger.warning(f"Optimistic locking conflict for task: {feature_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has been modified. Please refresh and try again."
            )
        logger.error(f"GitHub API error updating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update task: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error updating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


# ========================================================================
# T114: Get Document Template Endpoint
# ========================================================================

@router.get("/{feature_id}/template/{doc_type}", response_model=DocumentTemplate, status_code=status.HTTP_200_OK)
async def get_template(
    feature_id: str,
    doc_type: str,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Get document template for creating new documents.
    
    Implements T114:
    - Returns template for spec, plan, or task
    - Pre-fills with feature information
    - Used when document doesn't exist yet
    
    Args:
        feature_id: Feature identifier (for template context)
        doc_type: Document type (spec, plan, task)
        github_client: Authenticated GitHub client
    
    Returns:
        DocumentTemplate with template content
    
    Raises:
        HTTPException: If feature not found or invalid doc type
    """
    try:
        # Validate document type
        if doc_type not in DOCUMENT_TEMPLATES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type. Must be one of: {list(DOCUMENT_TEMPLATES.keys())}"
            )
        
        # Get feature for context
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        # Get template and fill in feature details
        template_content = DOCUMENT_TEMPLATES[doc_type]
        filled_content = template_content.format(
            feature_title=feature.title,
            branch_name=feature.branch_name,
            created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        logger.info(f"Generated {doc_type} template for feature {feature_id}")
        
        return DocumentTemplate(
            name=doc_type,
            content=filled_content
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


# ========================================================================
# T115: Create Document from Template Endpoint
# ========================================================================

@router.post("/{feature_id}/document/{doc_type}", response_model=DocumentUpdateResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    feature_id: str,
    doc_type: str,
    message: Optional[str] = None,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Create a new document from template for a feature.
    
    Implements T115:
    - Creates spec, plan, or task document from template
    - Initializes with feature context
    - Saves to GitHub
    
    Args:
        feature_id: Feature identifier
        doc_type: Document type (spec, plan, task)
        message: Optional custom commit message
        github_client: Authenticated GitHub client
    
    Returns:
        DocumentUpdateResponse with SHA and path
    
    Raises:
        HTTPException: If feature not found, invalid type, or creation fails
    """
    try:
        # Validate document type
        if doc_type not in DOCUMENT_TEMPLATES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type. Must be one of: {list(DOCUMENT_TEMPLATES.keys())}"
            )
        
        # Get feature
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        # Generate document content from template
        template_content = DOCUMENT_TEMPLATES[doc_type]
        doc_content = template_content.format(
            feature_title=feature.title,
            branch_name=feature.branch_name,
            created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Determine path
        doc_path = DOCUMENT_PATHS[doc_type].format(branch=feature.branch_name)
        
        # Use provided message or generate one
        commit_message = message or f"Initialize {doc_type} for feature: {feature.title}"
        
        # Write to GitHub
        new_sha = await github_client.write_file(
            repo_full_name=feature.repository_full_name,
            path=doc_path,
            content=doc_content,
            message=commit_message,
            branch=feature.branch_name,
            sha=None  # Create new file
        )
        
        # Update feature metadata based on document type
        if doc_type == "spec":
            feature.spec_path = doc_path
        elif doc_type == "plan":
            feature.plan_path = doc_path
        elif doc_type == "task":
            feature.task_path = doc_path
        
        feature.updated_at = datetime.utcnow()
        storage.save_feature(feature)
        
        logger.info(f"Created {doc_type} document for feature {feature_id}")
        
        return DocumentUpdateResponse(
            sha=new_sha,
            path=doc_path,
            updated_at=datetime.utcnow(),
            message=f"{doc_type.capitalize()} document created successfully"
        )
        
    except HTTPException:
        raise
    except GitHubAPIError as e:
        logger.error(f"GitHub API error creating document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create document: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error creating document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


# ========================================================================
# T116: Get All Documents Endpoint (convenience)
# ========================================================================

class AllDocumentsResponse(BaseModel):
    """Response containing all documents for a feature."""
    feature_id: str
    spec: Optional[DocumentResponse] = None
    plan: Optional[DocumentResponse] = None
    task: Optional[DocumentResponse] = None


@router.get("/{feature_id}/documents", response_model=AllDocumentsResponse, status_code=status.HTTP_200_OK)
async def get_all_documents(
    feature_id: str,
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Fetch all documents (spec, plan, task) for a feature in one request.
    
    Implements T116:
    - Fetches all three documents with minimal client requests
    - Returns only documents that exist (others null)
    - Useful for dashboard or loading feature details
    
    Args:
        feature_id: Feature identifier
        github_client: Authenticated GitHub client
    
    Returns:
        AllDocumentsResponse with all available documents
    
    Raises:
        HTTPException: If feature not found
    """
    try:
        # Get feature from storage
        feature: Optional[Feature] = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature not found: {feature_id}"
            )
        
        spec_doc = None
        plan_doc = None
        task_doc = None
        
        # Try to fetch each document (non-blocking if they don't exist)
        for doc_type, doc_var in [("spec", "spec_doc"), ("plan", "plan_doc"), ("task", "task_doc")]:
            try:
                doc_path = (
                    getattr(feature, f"{doc_type}_path") or
                    DOCUMENT_PATHS[doc_type].format(branch=feature.branch_name)
                )
                
                content, sha = await github_client.read_file(
                    repo_full_name=feature.repository_full_name,
                    path=doc_path,
                    branch=feature.branch_name,
                    use_cache=True
                )
                
                doc = DocumentResponse(
                    content=content,
                    sha=sha,
                    path=doc_path,
                    repository=feature.repository_full_name,
                    branch=feature.branch_name,
                    last_modified=feature.updated_at
                )
                
                if doc_type == "spec":
                    spec_doc = doc
                elif doc_type == "plan":
                    plan_doc = doc
                elif doc_type == "task":
                    task_doc = doc
                    
            except GitHubAPIError:
                # Document doesn't exist yet, that's fine
                pass
        
        logger.info(f"Retrieved all documents for feature {feature_id}")
        
        return AllDocumentsResponse(
            feature_id=feature_id,
            spec=spec_doc,
            plan=plan_doc,
            task=task_doc
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error fetching all documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch documents: {str(e)}"
        )


# ========================================================================
# Document Generation Endpoints (Copilot CLI Integration)
# ========================================================================

class GenerateDocumentRequest(BaseModel):
    """Request to generate document with Copilot CLI."""
    requirement_description: str = Field(..., description="Natural language feature requirement", min_length=10)
    enable_copilot: bool = Field(default=True, description="Use Copilot CLI enrichment")
    copilot_model: Optional[str] = Field(None, description="Copilot model name (e.g., gpt-4)")
    include_context: bool = Field(default=True, description="Include existing documents as context")
    operation_id: Optional[str] = Field(None, description="WebSocket operation ID for live updates")


async def _emit_ws_message(
    operation_id: str,
    sequence: int,
    message_type: MessageType,
    content: str,
    priority: MessagePriority = MessagePriority.NORMAL,
    is_final: bool = False,
    data: Optional[dict] = None,
    collapsible: bool = False,
) -> None:
    message = WebSocketMessage(
        message_id=str(uuid.uuid4()),
        operation_id=operation_id,
        sequence=sequence,
        type=message_type,
        content=content,
        data=data,
        priority=priority,
        is_final=is_final,
        collapsible=collapsible,
    )
    await connection_manager.broadcast_to_operation(operation_id, message)


async def _run_with_progress(
    operation_id: Optional[str],
    sequence: int,
    progress_message: str,
    func,
    *args,
    **kwargs
):
    if not operation_id:
        result = await asyncio.to_thread(func, *args, **kwargs)
        return result, sequence

    await _emit_ws_message(
        operation_id=operation_id,
        sequence=sequence,
        message_type=MessageType.PROGRESS,
        content=progress_message,
    )
    sequence += 1
    result = await asyncio.to_thread(func, *args, **kwargs)
    return result, sequence


class GenerateDocumentResponse(BaseModel):
    """Response from document generation."""
    content: str = Field(..., description="Generated document content")
    used_copilot: bool = Field(..., description="Whether Copilot CLI was used")
    model_used: Optional[str] = Field(None, description="Copilot model used")
    message: str = Field(default="Document generated successfully")


@router.post("/{feature_id}/generate-spec", response_model=GenerateDocumentResponse, status_code=status.HTTP_200_OK)
async def generate_spec(
    feature_id: str,
    request: GenerateDocumentRequest,
    x_session_id: str = Header(..., description="Session ID"),
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Generate specification document with Copilot CLI enrichment.
    
    Workflow:
    1. Retrieve feature metadata
    2. Use DocumentGenerator with Copilot CLI
    3. Return generated content (user must save manually)
    
    Args:
        feature_id: Feature ID
        request: Generation request with requirement description
        x_session_id: Session ID
        github_client: Authenticated GitHub client
    
    Returns:
        GenerateDocumentResponse with generated spec content
    """
    try:
        # Get feature from storage
        feature = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature {feature_id} not found"
            )
        
        logger.info(f"Generating spec for feature {feature_id} with Copilot: {request.enable_copilot}")
        sequence = 0
        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.EXECUTION,
                content="Starting spec generation...",
            )
            sequence += 1
        
        # Create document generator
        doc_gen = DocumentGenerator(
            enable_copilot=request.enable_copilot,
            model_name=request.copilot_model
        )
        
        # Generate spec
        if request.operation_id and request.enable_copilot:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.THINKING,
                content="Copilot CLI is generating your specification...",
                collapsible=True,
            )
            sequence += 1
        spec_content, sequence = await _run_with_progress(
            request.operation_id,
            sequence,
            "Generating specification...",
            doc_gen.generate_spec,
            requirement=request.requirement_description,
            feature_title=feature.title,
            branch_name=feature.branch_name,
            repository_name=feature.repository_full_name
        )

        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.COMPLETE,
                content="Spec generation complete. Review and save when ready.",
                is_final=True,
            )
        
        return GenerateDocumentResponse(
            content=spec_content,
            used_copilot=request.enable_copilot and doc_gen.copilot_available,
            model_used=request.copilot_model if request.enable_copilot else None,
            message="Spec generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate spec: {str(e)}")
        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=999,
                message_type=MessageType.ERROR,
                content=f"Spec generation failed: {str(e)}",
                priority=MessagePriority.HIGH,
                is_final=True,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate spec: {str(e)}"
        )


@router.post("/{feature_id}/generate-plan", response_model=GenerateDocumentResponse, status_code=status.HTTP_200_OK)
async def generate_plan(
    feature_id: str,
    request: GenerateDocumentRequest,
    x_session_id: str = Header(..., description="Session ID"),
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Generate implementation plan with Copilot CLI enrichment.
    
    Optionally includes spec content as context for better plan generation.
    
    Args:
        feature_id: Feature ID
        request: Generation request
        x_session_id: Session ID
        github_client: Authenticated GitHub client
    
    Returns:
        GenerateDocumentResponse with generated plan content
    """
    try:
        # Get feature from storage
        feature = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature {feature_id} not found"
            )
        
        logger.info(f"Generating plan for feature {feature_id} with Copilot: {request.enable_copilot}")
        sequence = 0
        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.EXECUTION,
                content="Starting plan generation...",
            )
            sequence += 1
        
        # Load spec for context (if requested)
        spec_content = None
        if request.include_context and feature.spec_path:
            try:
                spec_content, _ = await github_client.read_file(
                    repo_full_name=feature.repository_full_name,
                    path=feature.spec_path,
                    branch=feature.branch_name
                )
                logger.info(f"Loaded spec context ({len(spec_content)} chars)")
                if request.operation_id:
                    await _emit_ws_message(
                        operation_id=request.operation_id,
                        sequence=sequence,
                        message_type=MessageType.PROGRESS,
                        content="Loaded spec context for plan generation.",
                    )
                    sequence += 1
            except GitHubAPIError:
                logger.warning("Spec not found, generating plan without spec context")
        
        # Create document generator
        doc_gen = DocumentGenerator(
            enable_copilot=request.enable_copilot,
            model_name=request.copilot_model
        )
        
        # Generate plan
        if request.operation_id and request.enable_copilot:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.THINKING,
                content="Copilot CLI is drafting the implementation plan...",
                collapsible=True,
            )
            sequence += 1
        plan_content, sequence = await _run_with_progress(
            request.operation_id,
            sequence,
            "Generating implementation plan...",
            doc_gen.generate_plan,
            requirement=request.requirement_description,
            feature_title=feature.title,
            branch_name=feature.branch_name,
            repository_name=feature.repository_full_name,
            spec_content=spec_content
        )

        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.COMPLETE,
                content="Plan generation complete. Review and save when ready.",
                is_final=True,
            )
        
        return GenerateDocumentResponse(
            content=plan_content,
            used_copilot=request.enable_copilot and doc_gen.copilot_available,
            model_used=request.copilot_model if request.enable_copilot else None,
            message="Plan generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate plan: {str(e)}")
        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=999,
                message_type=MessageType.ERROR,
                content=f"Plan generation failed: {str(e)}",
                priority=MessagePriority.HIGH,
                is_final=True,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate plan: {str(e)}"
        )


@router.post("/{feature_id}/generate-task", response_model=GenerateDocumentResponse, status_code=status.HTTP_200_OK)
async def generate_task(
    feature_id: str,
    request: GenerateDocumentRequest,
    x_session_id: str = Header(..., description="Session ID"),
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Generate task breakdown with Copilot CLI enrichment.
    
    Optionally includes spec and plan content as context for better task generation.
    
    Args:
        feature_id: Feature ID
        request: Generation request
        x_session_id: Session ID
        github_client: Authenticated GitHub client
    
    Returns:
        GenerateDocumentResponse with generated tasks content
    """
    try:
        # Get feature from storage
        feature = storage.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature {feature_id} not found"
            )
        
        logger.info(f"Generating tasks for feature {feature_id} with Copilot: {request.enable_copilot}")
        sequence = 0
        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.EXECUTION,
                content="Starting task generation...",
            )
            sequence += 1
        
        # Load spec and plan for context (if requested)
        spec_content = None
        plan_content = None
        
        if request.include_context:
            # Load spec
            if feature.spec_path:
                try:
                    spec_content, _ = await github_client.read_file(
                        repo_full_name=feature.repository_full_name,
                        path=feature.spec_path,
                        branch=feature.branch_name
                    )
                    logger.info(f"Loaded spec context ({len(spec_content)} chars)")
                    if request.operation_id:
                        await _emit_ws_message(
                            operation_id=request.operation_id,
                            sequence=sequence,
                            message_type=MessageType.PROGRESS,
                            content="Loaded spec context for task generation.",
                        )
                        sequence += 1
                except GitHubAPIError:
                    logger.warning("Spec not found")
            
            # Load plan
            if feature.plan_path:
                try:
                    plan_content, _ = await github_client.read_file(
                        repo_full_name=feature.repository_full_name,
                        path=feature.plan_path,
                        branch=feature.branch_name
                    )
                    logger.info(f"Loaded plan context ({len(plan_content)} chars)")
                    if request.operation_id:
                        await _emit_ws_message(
                            operation_id=request.operation_id,
                            sequence=sequence,
                            message_type=MessageType.PROGRESS,
                            content="Loaded plan context for task generation.",
                        )
                        sequence += 1
                except GitHubAPIError:
                    logger.warning("Plan not found")
        
        # Create document generator
        doc_gen = DocumentGenerator(
            enable_copilot=request.enable_copilot,
            model_name=request.copilot_model
        )
        
        # Generate tasks
        if request.operation_id and request.enable_copilot:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.THINKING,
                content="Copilot CLI is generating task breakdown...",
                collapsible=True,
            )
            sequence += 1
        task_content, sequence = await _run_with_progress(
            request.operation_id,
            sequence,
            "Generating task breakdown...",
            doc_gen.generate_tasks,
            requirement=request.requirement_description,
            feature_title=feature.title,
            branch_name=feature.branch_name,
            repository_name=feature.repository_full_name,
            spec_content=spec_content,
            plan_content=plan_content
        )

        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=sequence,
                message_type=MessageType.COMPLETE,
                content="Task generation complete. Review and save when ready.",
                is_final=True,
            )
        
        return GenerateDocumentResponse(
            content=task_content,
            used_copilot=request.enable_copilot and doc_gen.copilot_available,
            model_used=request.copilot_model if request.enable_copilot else None,
            message="Tasks generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate tasks: {str(e)}")
        if request.operation_id:
            await _emit_ws_message(
                operation_id=request.operation_id,
                sequence=999,
                message_type=MessageType.ERROR,
                content=f"Task generation failed: {str(e)}",
                priority=MessagePriority.HIGH,
                is_final=True,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tasks: {str(e)}"
        )

