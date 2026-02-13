"""
Copilot SDLC POC - Streamlit UX for Natural Language Spec Generation

This application provides a minimal POC interface for business users to:
1. Enter natural language requirements
2. Invoke /specify command from Speckit  
3. View agent activity in real-time
4. Review and update generated specifications

Architecture:
- Frontend: Streamlit (web UI)
- Backend: Speckit CLI invocation via subprocess
- Environment: copilotcompanion (pyenv Python 3.13.11)
- Data: Git-backed (specs/ directory)

Constitution: v1.0.1 - Streamlit POC Phase
"""

import streamlit as st
import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import threading
import queue
import re

# ============================================================================
# Configuration
# ============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent  # /Users/rajeshhassija/Documents/GitHub/copilotcli
SPECS_DIR = REPO_ROOT / "specs" / "001-spec-generator"
SPEC_FILE = SPECS_DIR / "spec.md"
PYTHON_ENV = os.environ.get("VIRTUAL_ENV", "copilotcompanion")

st.set_page_config(
    page_title="Copilot SDLC - Spec Generator POC",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# State Management (Streamlit Session State)
# ============================================================================

if "spec_content" not in st.session_state:
    st.session_state.spec_content = None
if "activity_log" not in st.session_state:
    st.session_state.activity_log = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "last_requirement" not in st.session_state:
    st.session_state.last_requirement = ""
if "status_message" not in st.session_state:
    st.session_state.status_message = ""

# ============================================================================
# Utility Functions
# ============================================================================

def get_speckit_command():
    """Get the /specify command from Speckit CLI."""
    # In a real implementation, this would invoke: speckit /specify <requirement>
    # For POC, we'll simulate or invoke the actual command if available
    return "speckit"

def stream_command_output(cmd, callback=None):
    """
    Stream subprocess output in real-time to callback.
    
    Args:
        cmd: Command to execute (list of strings)
        callback: Function to call with each output line
    
    Returns:
        (return_code, all_output_text)
    """
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout for unified stream
            text=True,
            bufsize=1  # Line-buffered
        )
        
        all_output = []
        for line in process.stdout:
            line = line.rstrip('\n')
            all_output.append(line)
            if callback:
                callback(line)
        
        return_code = process.wait()
        return return_code, "\n".join(all_output)
    
    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        if callback:
            callback(error_msg)
        return 1, error_msg

def execute_specify_command(requirement: str):
    """
    Execute /specify command with the given requirement.
    
    This is a stub that would invoke: speckit /specify "requirement"
    For POC, we'll prepare the invocation (actual CLI integration TBD).
    
    Args:
        requirement: User's natural language requirement
    
    Yields:
        (status_str, is_complete_bool)
    """
    yield ("Preparing specification generation...", False)
    
    # Validate requirement
    if not requirement or not requirement.strip():
        yield ("Error: Requirement cannot be empty", True)
        return
    
    # Prepare command - this would be the actual speckit invocation
    # For POC, we'll use a placeholder that shows how CLI would be called
    cmd = ["echo", f"[SPECKIT /specify] Processing requirement: {requirement}"]
    
    # In production, this would be:
    # cmd = ["speckit", "/specify", requirement]
    # cmd_str = " ".join(cmd)
    # Note: actual --json option would be: speckit /specify --json requirement
    
    try:
        # Create output directory
        SPECS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Execute command and stream output
        def log_output(line):
            st.session_state.activity_log.append(line)
        
        yield ("Executing /specify command...", False)
        return_code, output = stream_command_output(cmd, callback=log_output)
        
        if return_code != 0:
            yield (f"Command failed with exit code {return_code}", True)
            return
        
        # Generate sample spec.md for POC demo
        # In real implementation, /specify would generate this
        sample_spec = f"""# Feature Specification: {requirement}

**Feature Branch**: `001-spec-generator`  
**Created**: {datetime.now().strftime('%Y-%m-%d')}  
**Status**: Draft  
**Input**: User requirement: "{requirement}"

## User Scenarios & Testing

### User Story 1 - Primary Implementation (Priority: P1)

A user can complete the primary use case described in the requirement.

**Acceptance Scenarios**:
1. **Given** the system is ready, **When** user interacts, **Then** the feature works as described
2. **Given** the feature is complete, **When** user tests it, **Then** it meets the requirement

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement the described feature
- **FR-002**: System MUST validate user inputs appropriately
- **FR-003**: System MUST provide clear feedback to users

### Key Entities

- **Requirement**: {requirement}

## Success Criteria

### Measurable Outcomes

- **SC-001**: Feature successfully implements the user requirement
- **SC-002**: All acceptance scenarios pass
- **SC-003**: No critical errors during execution

---
*Generated by Copilot SDLC POC - {datetime.now().isoformat()}*
"""
        
        # Write spec.md (simulated - in real implementation, /specify would produce this)
        with open(SPEC_FILE, 'w') as f:
            f.write(sample_spec)
        
        st.session_state.spec_content = sample_spec
        yield (f"✅ Specification generated successfully: {SPEC_FILE}", True)
        
    except Exception as e:
        yield (f"❌ Error: {str(e)}", True)

# ============================================================================
# UI Components
# ============================================================================

def render_header():
    """Render page header."""
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1>🚀 Copilot SDLC - Spec Generator POC</h1>
        <p><em>Natural Language → Specification Generation (Constitution v1.0.1)</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()

def render_input_section():
    """Render requirement input section."""
    st.subheader("📝 Enter Your Requirement")
    
    requirement = st.text_area(
        label="What feature or capability do you want to build?",
        placeholder="Example: Create a user authentication system with password reset",
        height=100,
        key="requirement_input"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 Tip: Be specific and detailed. The clearer your requirement, the better the specification.")
    with col2:
        submit_button = st.button(
            "📤 Submit Requirement",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.is_processing
        )
    
    return requirement, submit_button

def render_activity_log():
    """Render real-time activity log."""
    st.subheader("🔄 Agent Activity (Real-Time)")
    
    activity_container = st.container(border=True)
    
    with activity_container:
        if st.session_state.activity_log:
            for line in st.session_state.activity_log:
                st.code(line, language="text")
        else:
            st.info("Activity will appear here when processing begins...")
    
    return activity_container

def render_status():
    """Render status message."""
    if st.session_state.status_message:
        if "✅" in st.session_state.status_message or "successfully" in st.session_state.status_message.lower():
            st.success(st.session_state.status_message)
        elif "❌" in st.session_state.status_message or "error" in st.session_state.status_message.lower():
            st.error(st.session_state.status_message)
        else:
            st.info(st.session_state.status_message)

def render_spec_viewer():
    """Render specification viewer."""
    if st.session_state.spec_content:
        st.subheader("📄 Generated Specification")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(st.session_state.spec_content)
        with col2:
            st.markdown("**📌 Spec Info:**")
            st.write(f"Location: `{SPEC_FILE}`")
            st.write(f"Status: `Draft`")
            if st.button("🔄 Refresh Spec"):
                st.rerun()

# ============================================================================
# Main App Logic
# ============================================================================

def main():
    """Main application entry point."""
    
    render_header()
    
    # Left column: Input and activity
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        requirement, submit_button = render_input_section()
        render_activity_log()
    
    with col_right:
        render_status()
        render_spec_viewer()
    
    # Process form submission
    if submit_button:
        st.session_state.is_processing = True
        st.session_state.activity_log = []
        st.session_state.status_message = ""
        st.session_state.last_requirement = requirement
        
        try:
            # Execute /specify command and stream output
            for status, is_complete in execute_specify_command(requirement):
                st.session_state.status_message = status
                st.rerun()
                if is_complete:
                    break
        
        except Exception as e:
            st.session_state.status_message = f"❌ Unexpected error: {str(e)}"
        
        finally:
            st.session_state.is_processing = False
        
        st.rerun()
    
    # Sidebar: Info & Configuration
    with st.sidebar:
        st.markdown("### 📚 POC Information")
        st.info("""
        **Phase**: Minimal POC  
        **Goal**: Validate natural language → `/specify` → spec generation workflow  
        **Environment**: copilotcompanion (pyenv)  
        **Status**: Beta Testing
        """)
        
        st.markdown("### ⚙️ Configuration")
        st.write(f"**Repo Root**: `{REPO_ROOT}`")
        st.write(f"**Specs Dir**: `{SPECS_DIR}`")
        st.write(f"**Python**: `{sys.version.split()[0]}`")
        
        st.markdown("### 📖 How It Works")
        st.markdown("""
        1. **Enter** your feature requirement in plain English
        2. **Click** "Submit Requirement"
        3. **Watch** agent activity stream in real-time
        4. **Review** generated specification when complete
        5. **Request** changes by submitting updated requirement
        """)
        
        st.divider()
        
        if st.button("🔄 Clear Activity Log"):
            st.session_state.activity_log = []
            st.session_state.spec_content = None
            st.rerun()

if __name__ == "__main__":
    main()
