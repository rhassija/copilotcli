"""
Copilot SDLC POC - Streamlit UX with Speckit + Copilot CLI enrichment.
Creates feature branches and fills specs using Copilot when available.

Notes for migration:
- Speckit provides scaffolding; Copilot CLI enriches content.
- The app is a thin orchestrator with minimal business logic.
- Replace CLI calls with SDK calls when available.
"""

import streamlit as st
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import sys
import os

# Configuration
REPO_ROOT = Path(__file__).parent.parent.parent
SPECS_DIR = REPO_ROOT / "specs"
COPILOT_PATH = Path.home() / "Library/Application Support/Code/User/globalStorage/github.copilot-chat/copilotCli/copilot"

st.set_page_config(
    page_title="Copilot SDLC - Spec Generator POC",
    page_icon="🚀",
    layout="wide",
)

# Initialize session state (kept minimal for Streamlit rerun model)
if "processing" not in st.session_state:
    st.session_state.processing = False
if "activity_lines" not in st.session_state:
    st.session_state.activity_lines = []
if "spec_text" not in st.session_state:
    st.session_state.spec_text = None
if "done" not in st.session_state:
    st.session_state.done = False
if "current_requirement" not in st.session_state:
    st.session_state.current_requirement = None
if "step_index" not in st.session_state:
    st.session_state.step_index = 0
if "error_message" not in st.session_state:
    st.session_state.error_message = None
if "feature_branch" not in st.session_state:
    st.session_state.feature_branch = None
if "use_copilot" not in st.session_state:
    st.session_state.use_copilot = True
if "model_name" not in st.session_state:
    st.session_state.model_name = ""

# ============================================================================
# Helper Functions
# ============================================================================

def run_speckit_command(requirement: str):
    """
    Execute the Speckit workflow:
    1. Create feature branch with create-new-feature.sh
    2. Generate spec.md from the template
    """
    try:
        yield "🔄 Initializing Speckit specification engine..."
        yield f"📝 Processing requirement: '{requirement[:50]}{'...' if len(requirement) > 50 else ''}'"
        
        # Step 1: Create feature branch using Speckit's script
        yield "🌳 Creating feature branch..."
        
        create_feature_script = REPO_ROOT / ".specify/scripts/bash/create-new-feature.sh"
        if not create_feature_script.exists():
            yield "❌ Speckit scripts not found. Run: uvx --from git+https://github.com/github/spec-kit.git specify init ."
            return None
        
        # Run create-new-feature.sh with JSON output to capture branch name
        cmd = [
            "bash",
            str(create_feature_script),
            "--json",
            requirement
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(REPO_ROOT)
        )
        
        # Capture output
        stdout, stderr = process.communicate()
        
        if process.returncode != 0 and stderr:
            yield f"📊 Branch creation message: {stderr.strip()[:100]}"
        
        # Parse JSON output to get branch name
        feature_branch = None
        spec_file = None
        try:
            for line in stdout.split('\n'):
                if line.strip().startswith('{'):
                    data = json.loads(line)
                    if "BRANCH_NAME" in data:
                        feature_branch = data["BRANCH_NAME"]
                        st.session_state.feature_branch = feature_branch
                        yield f"✅ Branch created: {feature_branch}"
                    if "SPEC_FILE" in data:
                        spec_file = data["SPEC_FILE"]
        except json.JSONDecodeError:
            pass
        
        if not spec_file:
            yield "❌ Could not determine spec file path"
            return None
        
        yield "📄 Generating specification from template..."
        time.sleep(0.5)

        # Step 2: Generate spec.md (Copilot-enriched when available)
        template_path = REPO_ROOT / ".specify/templates/spec-template.md"
        template_text = template_path.read_text() if template_path.exists() else ""

        spec_content = None
        if st.session_state.use_copilot:
            yield "🤖 Enriching spec with Copilot CLI..."
            spec_content = enrich_spec_with_copilot(
                requirement=requirement,
                template_text=template_text,
                model_name=st.session_state.model_name.strip() or None,
            )
            if spec_content:
                yield "✅ Copilot enrichment complete"
            else:
                yield "⚠️ Copilot enrichment unavailable, using template defaults"

        if not spec_content:
            spec_content = generate_spec_from_template(requirement)
        
        # Write spec file to the feature folder created by Speckit
        spec_path = Path(spec_file)
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(spec_content)
        
        yield "✅ Specification generated successfully!"
        return spec_content
            
    except Exception as e:
        yield f"❌ Error: {str(e)[:100]}"
        return None


def generate_spec_from_template(requirement: str) -> str:
    """Generate a proper specification from the Speckit template."""
    template_path = REPO_ROOT / ".specify/templates/spec-template.md"
    
    if not template_path.exists():
        # Fallback if template not found
        return f"""# Feature Specification: {requirement}

## User Scenarios & Testing

### User Story 1 - Implementation (Priority: P1)

{requirement}

**Acceptance Scenarios**:
- Feature works as described
- User can interact with it
- All requirements are met

## Functional Requirements

- System MUST implement: {requirement}
- Validate user inputs
- Provide clear feedback
- Handle errors gracefully

## Success Criteria

- Feature is complete and tested
- No critical errors
- Performance is acceptable
"""
    
    # Read template
    template = template_path.read_text()
    
    # Generate a minimal, readable spec based on the template
    from datetime import datetime
    
    # Create user stories from requirement
    spec = template
    spec = spec.replace("[FEATURE NAME]", requirement)
    spec = spec.replace("[###-feature-name]", st.session_state.feature_branch or "###-feature")
    spec = spec.replace("[DATE]", datetime.now().strftime('%Y-%m-%d'))
    spec = spec.replace("$ARGUMENTS", requirement)
    
    # Add basic user stories if template format is present
    if "[Brief Title]" in spec:
        story1 = f"""### User Story 1 - Implement {requirement[:40]} (Priority: P1)

The system must implement: {requirement}

**Why this priority**: This is the core functionality requested.

**Independent Test**: User can {requirement.lower()} without errors

**Acceptance Scenarios**:
1. **Given** user wants to use this feature, **When** they submit a request, **Then** the system processes it successfully
2. **Given** valid input, **When** feature is used, **Then** the output is correct
"""
        spec = spec.replace("### User Story 1 - [Brief Title]", story1)
    
    return spec


def enrich_spec_with_copilot(requirement: str, template_text: str, model_name: str | None) -> str | None:
    """Use Copilot CLI to generate a filled spec from the template."""
    if not COPILOT_PATH.exists():
        return None

    prompt_parts = [
        "You are generating a product specification for non-technical stakeholders.",
        "Fill the template completely with clear, testable requirements.",
        "Do NOT include implementation details, frameworks, or code.",
        "Return only the completed markdown spec.",
        "",
        "User requirement:",
        requirement,
        "",
        "Template:",
        template_text or "(No template found. Create a full spec with sections for User Scenarios & Testing, Functional Requirements, Success Criteria, Assumptions, and Out of Scope.)",
    ]
    prompt = "\n".join(prompt_parts)

    # CLI call is the integration seam; replace with SDK calls in production.
    cmd = [str(COPILOT_PATH), "-p", prompt, "--allow-all-tools"]
    if model_name:
        cmd.extend(["--model", model_name])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        if result.returncode != 0:
            return None

        output = (result.stdout or "").strip()
        if not output:
            return None

        return output
    except Exception:
        return None

def read_generated_spec(feature_branch: str = None):
    """
    Read the generated spec.md file from the feature directory.
    """
    try:
        if feature_branch:
            spec_path = REPO_ROOT / "specs" / feature_branch / "spec.md"
        else:
            # Fallback: look for most recent spec.md
            specs_dir = REPO_ROOT / "specs"
            spec_paths = list(specs_dir.glob("*/spec.md"))
            if not spec_paths:
                return None
            spec_path = max(spec_paths, key=lambda p: p.stat().st_mtime)
        
        if spec_path.exists():
            return spec_path.read_text()
        return None
    except Exception as e:
        st.error(f"Error reading spec: {e}")
        return None

# ============================================================================
# Layout
# ============================================================================

st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <h1>🚀 Copilot SDLC - Spec Generator POC</h1>
    <p>Real Speckit Integration | Natural Language → Specification</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# Two columns
col_left, col_right = st.columns([1, 1], gap="large")

# ============================================================================
# LEFT COLUMN
# ============================================================================

with col_left:
    st.subheader("📝 Enter Your Requirement")
    
    requirement = st.text_area(
        "What feature do you want to build?",
        placeholder="Example: Create a user authentication system with password reset",
        height=100,
        disabled=st.session_state.processing,
    )
    
    submit_btn = st.button(
        "📤 Submit",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.processing or not requirement.strip(),
    )
    
    st.subheader("🔄 Agent Activity")
    
    # Activity log container
    with st.container(border=True, height=350):
        if st.session_state.activity_lines:
            for line in st.session_state.activity_lines:
                if line.startswith("✅"):
                    st.success(line)
                elif line.startswith("❌"):
                    st.error(line)
                elif line.startswith("✓") or line.startswith("🌳"):
                    st.info(line)
                else:
                    st.write(line)
        else:
            st.info("👆 Submit a requirement to see activity...")

# ============================================================================
# RIGHT COLUMN
# ============================================================================

with col_right:
    if st.session_state.processing:
        st.info("⏳ Speckit is processing your requirement...")
    elif st.session_state.done:
        st.success("✅ Specification generated successfully!")
        if st.session_state.feature_branch:
            st.caption(f"Branch: `{st.session_state.feature_branch}`")
        if st.session_state.use_copilot:
            model_label = st.session_state.model_name.strip() or "default"
            st.caption(f"Copilot model: {model_label}")
    
    if st.session_state.error_message:
        st.error(f"Error: {st.session_state.error_message}")
    
    if st.session_state.spec_text:
        st.subheader("📄 Generated Specification")
        with st.container(border=True, height=400):
            st.markdown(st.session_state.spec_text)

# ============================================================================
# Main Processing Logic
# ============================================================================

# Step 1: Handle submit button (starts a new run)
if submit_btn:
    st.session_state.current_requirement = requirement
    st.session_state.processing = True
    st.session_state.activity_lines = []
    st.session_state.done = False
    st.session_state.step_index = 0
    st.session_state.error_message = None
    st.session_state.feature_branch = None
    st.rerun()

# Step 2: Process ONE step per rerun (prevents infinite rerun loops)
if st.session_state.processing and not st.session_state.done:
    # First time - start the generator
    if "generator" not in st.session_state:
        st.session_state.generator = run_speckit_command(st.session_state.current_requirement)
    
    # Get next activity update
    try:
        activity = next(st.session_state.generator)
        st.session_state.activity_lines.append(activity)
        time.sleep(0.1)
        st.rerun()
    except StopIteration as e:
        # Generator exhausted - processing complete
        spec_content = read_generated_spec(st.session_state.feature_branch)
        
        if spec_content:
            st.session_state.spec_text = spec_content
            st.session_state.done = True
        else:
            st.session_state.error_message = "Could not read generated specification file"
            st.session_state.done = True
        
        st.session_state.processing = False
        del st.session_state.generator
        st.rerun()

# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.markdown("### 📚 About")
    st.info("""
    **Phase**: POC with Real Speckit
    
    **Goal**: Natural language → Real specification via Speckit
    
    **Status**: 🔴 Live Speckit Integration
    """)
    
    st.markdown("### ⚙️ System")
    st.write(f"Repo: `{REPO_ROOT.name}`")
    st.write(f"Specs: `specs/`")
    st.write(f"Tool: Speckit via uvx")
    
    st.markdown("### 🔧 Tools")
    
    # Check uvx
    try:
        result = subprocess.run(["which", "uvx"], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("✅ uvx available")
        else:
            st.warning("⚠️ uvx not found")
    except:
        st.warning("⚠️ uvx check failed")
    
    # Check Copilot CLI
    if COPILOT_PATH.exists():
        st.success("✅ Copilot CLI available")
    else:
        st.warning("⚠️ Copilot CLI not found")

    # Check Copilot auth (best-effort via env tokens)
    token_envs = ["COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"]
    has_token = any(os.getenv(name) for name in token_envs)
    if has_token:
        st.success("✅ Copilot auth token detected")
    else:
        st.info("ℹ️ Copilot auth not detected (run `copilot` then `/login`) ")

    st.markdown("### 🤖 Copilot Enrichment")
    st.session_state.use_copilot = st.checkbox(
        "Enable Copilot enrichment",
        value=st.session_state.use_copilot,
        help="Uses Copilot CLI to fill the spec template",
    )
    st.session_state.model_name = st.text_input(
        "Model (optional)",
        value=st.session_state.model_name,
        placeholder="e.g., gpt-5",
        help="Leave empty to use Copilot default model",
    )
    
    st.markdown("### 📖 Steps")
    st.markdown("""
    1. Type requirement
    2. Click Submit
    3. Watch Speckit process (left)
    4. Review generated spec (right)
    """)
    
    if st.button("🔄 Clear"):
        st.session_state.activity_lines = []
        st.session_state.spec_text = None
        st.session_state.processing = False
        st.session_state.done = False
        st.session_state.step_index = 0
        st.session_state.current_requirement = None
        st.session_state.error_message = None
        st.session_state.feature_branch = None
        if "generator" in st.session_state:
            del st.session_state.generator
        st.rerun()
