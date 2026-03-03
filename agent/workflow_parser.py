"""
Agent: Workflow Parser
Purpose: Parse markdown workflow files into structured step objects.
Maps step names to actual tool functions.
"""

import re
import os
import logging

logger = logging.getLogger(__name__)

WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows")


def load_workflow(workflow_name: str) -> dict:
    """
    Load and parse a workflow markdown file.
    Returns structured workflow with metadata and steps.
    """
    filepath = os.path.join(WORKFLOWS_DIR, workflow_name)
    if not filepath.endswith(".md"):
        filepath += ".md"

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Workflow not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    workflow = {
        "name": workflow_name.replace(".md", ""),
        "filepath": filepath,
        "objective": _extract_section(content, "Objective"),
        "inputs": _extract_section(content, "Required Inputs"),
        "tools": _extract_tools(content),
        "edge_cases": _extract_section(content, "Edge Cases"),
        "error_handling": _extract_section(content, "Error Handling"),
        "raw_content": content,
    }

    logger.info(f"Loaded workflow: {workflow['name']} with {len(workflow['tools'])} tool references")
    return workflow


def list_workflows() -> list[str]:
    """List all available workflow files."""
    if not os.path.exists(WORKFLOWS_DIR):
        return []
    return [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith(".md")]


def _extract_section(content: str, section_name: str) -> str:
    """Extract content under a ## heading."""
    pattern = rf'## {section_name}\s*\n(.*?)(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _extract_tools(content: str) -> list[str]:
    """Extract tool references (tools/*.py) from the workflow."""
    pattern = r'`tools/(\w+\.py)`'
    tools = re.findall(pattern, content)
    return list(dict.fromkeys(tools))  # Deduplicate while preserving order


def update_workflow_lessons(workflow_name: str, lesson: str):
    """Append a lesson learned to the workflow's Lessons Learned section."""
    filepath = os.path.join(WORKFLOWS_DIR, workflow_name)
    if not filepath.endswith(".md"):
        filepath += ".md"

    if not os.path.exists(filepath):
        logger.warning(f"Cannot update lessons — workflow not found: {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find and append to Lessons Learned section
    marker = "## Lessons Learned"
    if marker in content:
        content = content.replace(
            "(Agent updates this section as issues are discovered)",
            f"- {lesson}\n(Agent updates this section as issues are discovered)"
        )
    else:
        content += f"\n\n{marker}\n- {lesson}\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Updated lessons in {workflow_name}: {lesson}")
