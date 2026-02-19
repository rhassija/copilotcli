"""
Document generation service with Copilot CLI enrichment.

Provides:
- Template-based document generation
- Copilot CLI integration for content enrichment
- Spec/Plan/Task document generation
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentGenerationError(Exception):
    """Base exception for document generation errors."""
    pass


class CopilotCLINotFoundError(DocumentGenerationError):
    """Raised when Copilot CLI is not available."""
    pass


class DocumentGenerator:
    """
    Service for generating feature documents with Copilot CLI enrichment.
    
    Mirrors the POC workflow from src/ui/app.py:
    1. Load template from .specify/templates/
    2. Enrich with Copilot CLI if available
    3. Fallback to template-based generation
    """
    
    # Copilot CLI path (from VS Code installation)
    COPILOT_CLI_PATH = Path.home() / "Library/Application Support/Code/User/globalStorage/github.copilot-chat/copilotCli/copilot"
    
    # Template directory
    TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / ".specify/templates"
    
    def __init__(self, enable_copilot: bool = True, model_name: Optional[str] = None):
        """
        Initialize document generator.
        
        Args:
            enable_copilot: Whether to use Copilot CLI enrichment
            model_name: Copilot model name (e.g., "gpt-4", "claude-3.5-sonnet")
        """
        self.enable_copilot = enable_copilot
        self.model_name = model_name
        self.copilot_available = self.COPILOT_CLI_PATH.exists()
        
        if self.enable_copilot and not self.copilot_available:
            logger.warning(f"Copilot CLI not found at {self.COPILOT_CLI_PATH}")
    
    def generate_spec(
        self,
        requirement: str,
        feature_title: str,
        branch_name: str,
        repository_name: str
    ) -> str:
        """
        Generate specification document.
        
        Args:
            requirement: Natural language feature requirement
            feature_title: Feature title
            branch_name: Git branch name
            repository_name: Repository full name (owner/repo)
        
        Returns:
            Generated spec markdown content
        """
        template_path = self.TEMPLATE_DIR / "spec-template.md"
        template_text = self._load_template(template_path)
        
        # Try Copilot enrichment first
        if self.enable_copilot and self.copilot_available:
            logger.info("Attempting Copilot CLI enrichment for spec")
            enriched = self._enrich_with_copilot(
                requirement=requirement,
                template_text=template_text,
                document_type="specification"
            )
            if enriched:
                return enriched
            logger.warning("Copilot enrichment failed, falling back to template")
        
        # Fallback to template-based generation
        return self._generate_from_template(
            template_text=template_text,
            requirement=requirement,
            feature_title=feature_title,
            branch_name=branch_name,
            repository_name=repository_name
        )
    
    def generate_plan(
        self,
        requirement: str,
        feature_title: str,
        branch_name: str,
        repository_name: str,
        spec_content: Optional[str] = None
    ) -> str:
        """
        Generate implementation plan document.
        
        Args:
            requirement: Natural language feature requirement
            feature_title: Feature title
            branch_name: Git branch name
            repository_name: Repository full name
            spec_content: Optional spec content for context
        
        Returns:
            Generated plan markdown content
        """
        template_path = self.TEMPLATE_DIR / "plan-template.md"
        template_text = self._load_template(template_path)
        
        # Build prompt with spec context
        context = requirement
        if spec_content:
            context = f"Specification:\n{spec_content}\n\nRequirement: {requirement}"
        
        # Try Copilot enrichment
        if self.enable_copilot and self.copilot_available:
            logger.info("Attempting Copilot CLI enrichment for plan")
            enriched = self._enrich_with_copilot(
                requirement=context,
                template_text=template_text,
                document_type="implementation plan"
            )
            if enriched:
                return enriched
            logger.warning("Copilot enrichment failed, falling back to template")
        
        # Fallback to template
        return self._generate_from_template(
            template_text=template_text,
            requirement=requirement,
            feature_title=feature_title,
            branch_name=branch_name,
            repository_name=repository_name
        )
    
    def generate_tasks(
        self,
        requirement: str,
        feature_title: str,
        branch_name: str,
        repository_name: str,
        spec_content: Optional[str] = None,
        plan_content: Optional[str] = None
    ) -> str:
        """
        Generate task breakdown document.
        
        Args:
            requirement: Natural language feature requirement
            feature_title: Feature title
            branch_name: Git branch name
            repository_name: Repository full name
            spec_content: Optional spec content for context
            plan_content: Optional plan content for context
        
        Returns:
            Generated tasks markdown content
        """
        template_path = self.TEMPLATE_DIR / "tasks-template.md"
        template_text = self._load_template(template_path)
        
        # Build full context
        context_parts = [f"Requirement: {requirement}"]
        if spec_content:
            context_parts.append(f"Specification:\n{spec_content}")
        if plan_content:
            context_parts.append(f"Plan:\n{plan_content}")
        context = "\n\n".join(context_parts)
        
        # Try Copilot enrichment
        if self.enable_copilot and self.copilot_available:
            logger.info("Attempting Copilot CLI enrichment for tasks")
            enriched = self._enrich_with_copilot(
                requirement=context,
                template_text=template_text,
                document_type="task breakdown"
            )
            if enriched:
                return enriched
            logger.warning("Copilot enrichment failed, falling back to template")
        
        # Fallback to template
        return self._generate_from_template(
            template_text=template_text,
            requirement=requirement,
            feature_title=feature_title,
            branch_name=branch_name,
            repository_name=repository_name
        )
    
    def _load_template(self, template_path: Path) -> str:
        """Load template file or return default."""
        if template_path.exists():
            return template_path.read_text()
        
        # Default templates if files don't exist
        logger.warning(f"Template not found: {template_path}, using default")
        return self._get_default_template(template_path.stem)
    
    def _get_default_template(self, template_type: str) -> str:
        """Get default template content."""
        if "spec" in template_type:
            return """# Feature Specification

**Feature**: {feature_title}
**Branch**: {branch_name}
**Repository**: {repository_name}
**Created**: {created_at}

## Overview

{requirement}

## Requirements

- Requirement 1
- Requirement 2

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Technical Considerations

- Implementation approach

## Out of Scope

- Future enhancements
"""
        elif "plan" in template_type:
            return """# Implementation Plan

**Feature**: {feature_title}
**Branch**: {branch_name}
**Created**: {created_at}

## Summary

{requirement}

## Architecture

- Component 1
- Component 2

## Dependencies

- Dependency 1

## Tasks

1. Task 1
2. Task 2
"""
        else:  # tasks
            return """# Task Breakdown

**Feature**: {feature_title}
**Branch**: {branch_name}
**Created**: {created_at}

## Task List

- [ ] Task 1: {requirement}
- [ ] Task 2: Implementation
- [ ] Task 3: Testing
"""
    
    def _enrich_with_copilot(
        self,
        requirement: str,
        template_text: str,
        document_type: str
    ) -> Optional[str]:
        """
        Use Copilot CLI to enrich document with AI-generated content.
        
        Mirrors the enrich_spec_with_copilot function from POC.
        
        Args:
            requirement: User's natural language requirement
            template_text: Template markdown content
            document_type: Type of document (specification, plan, task breakdown)
        
        Returns:
            Enriched markdown content or None if failed
        """
        if not self.copilot_available:
            return None
        
        # Build prompt (same structure as POC)
        prompt_parts = [
            f"You are generating a {document_type} for non-technical stakeholders.",
            "Fill the template completely with clear, testable requirements.",
            "Do NOT include implementation details, frameworks, or code.",
            "Return only the completed markdown document.",
            "",
            "User requirement:",
            requirement,
            "",
            "Template:",
            template_text or f"(No template found. Create a full {document_type} with appropriate sections.)",
        ]
        prompt = "\n".join(prompt_parts)
        
        # Build command (same as POC)
        cmd = [str(self.COPILOT_CLI_PATH), "-p", prompt, "--allow-all-tools"]
        if self.model_name:
            cmd.extend(["--model", self.model_name])
        
        # Get repo root for cwd (like app.py does)
        repo_root = self.TEMPLATE_DIR.parent
        
        try:
            logger.info(f"Running Copilot CLI: {' '.join(cmd[:3])}... (model: {self.model_name or 'default'})")
            # Match app.py exactly: no timeout, with cwd
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(repo_root)
            )
            
            if result.returncode != 0:
                logger.error(f"Copilot CLI failed with code {result.returncode}: {result.stderr}")
                return None
            
            output = (result.stdout or "").strip()
            if not output:
                logger.warning("Copilot CLI returned empty output")
                return None
            
            logger.info(f"Copilot CLI enrichment successful ({len(output)} chars)")
            return output
        
        except Exception as e:
            logger.exception(f"Copilot CLI execution failed: {e}")
            return None
    
    def _generate_from_template(
        self,
        template_text: str,
        requirement: str,
        feature_title: str,
        branch_name: str,
        repository_name: str
    ) -> str:
        """
        Generate document from template with variable substitution.
        
        Args:
            template_text: Template markdown
            requirement: User requirement
            feature_title: Feature title
            branch_name: Branch name
            repository_name: Repository name
        
        Returns:
            Generated markdown content
        """
        # Replace template variables
        content = template_text
        replacements = {
            "{feature_title}": feature_title,
            "{requirement}": requirement,
            "{branch_name}": branch_name,
            "{repository_name}": repository_name,
            "{created_at}": datetime.utcnow().strftime("%Y-%m-%d"),
            "[FEATURE NAME]": feature_title,
            "[###-feature-name]": branch_name,
            "[DATE]": datetime.utcnow().strftime("%Y-%m-%d"),
            "$ARGUMENTS": requirement,
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        return content
