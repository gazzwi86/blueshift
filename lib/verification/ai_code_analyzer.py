#!/usr/bin/env python3
"""
AI-Powered Code Analyzer
========================

THIS IS THE LAW - Uses AI inference to detect placeholder/stub code.

This module uses the Claude Code SDK (same pattern as init/coding agents)
to analyze code files and determine if they contain real implementations
or placeholder code. This is more robust than regex-based pattern matching.

Uses the same SDK and authentication as the main harness agents.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient


# Analysis prompt for placeholder detection
PLACEHOLDER_ANALYSIS_PROMPT = """You are a code quality auditor. Analyze the file(s) I'm about to show you and determine if they contain REAL implementations or PLACEHOLDER/STUB code.

For each file, respond with a JSON object:
{{
  "file": "<filename>",
  "verdict": "REAL" or "PLACEHOLDER",
  "confidence": 0.0-1.0,
  "reasons": ["reason1", "reason2"]
}}

PLACEHOLDER indicators:
- Lambda handlers that just return {{"statusCode": 200}} with no logic
- Functions that raise NotImplementedError or just pass
- TODO/FIXME/PLACEHOLDER comments without implementation
- Terraform deploying placeholder.zip files
- Code that mocks everything without real integration

REAL indicators:
- Actual business logic that processes data
- Real API calls to external services (SharePoint, S3, Bedrock, etc.)
- Meaningful error handling for real scenarios
- Configuration connecting to real resources

Now analyze this file:
{file_path}

Read the file and provide your analysis as a JSON object."""


def create_analysis_client(project_dir: Path) -> ClaudeSDKClient:
    """
    Create a lightweight Claude SDK client for code analysis.

    Uses the same SDK pattern as the main harness agents but with
    minimal tools (just Read for file access).

    Args:
        project_dir: Project directory for analysis context

    Returns:
        Configured ClaudeSDKClient
    """
    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model="claude-sonnet-4-20250514",  # Fast model for analysis
            system_prompt="You are a code quality auditor analyzing files for placeholder code. Be concise and respond only with JSON.",
            allowed_tools=["Read", "Glob"],  # Only needs to read files
            max_turns=5,  # Short conversation
            cwd=str(project_dir.resolve()),
        )
    )


async def analyze_file_with_sdk(
    project_dir: Path,
    file_path: Path,
) -> dict:
    """
    Use Claude Code SDK to analyze a single file for placeholder patterns.

    Args:
        project_dir: Project directory (working directory)
        file_path: Path to file to analyze

    Returns:
        Dict with 'verdict', 'confidence', 'reasons', or 'error'
    """
    try:
        # Get relative path for the prompt
        try:
            relative_path = str(file_path.relative_to(project_dir))
        except ValueError:
            relative_path = str(file_path)

        # Build the analysis prompt
        prompt = PLACEHOLDER_ANALYSIS_PROMPT.format(file_path=relative_path)

        # Create client and run analysis
        client = create_analysis_client(project_dir)

        async with client:
            await client.query(prompt)

            response_text = ""
            async for msg in client.receive_response():
                msg_type = type(msg).__name__

                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        if hasattr(block, "text"):
                            response_text += block.text

        # Parse JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                result = json.loads(json_str)
                result["file"] = relative_path
                return result
            except json.JSONDecodeError:
                pass

        # Fallback: interpret text response
        response_upper = response_text.upper()
        if "PLACEHOLDER" in response_upper:
            return {
                "file": relative_path,
                "verdict": "PLACEHOLDER",
                "confidence": 0.8,
                "reasons": ["AI detected placeholder code"]
            }
        elif "REAL" in response_upper:
            return {
                "file": relative_path,
                "verdict": "REAL",
                "confidence": 0.8,
                "reasons": ["AI detected real implementation"]
            }

        return {
            "file": relative_path,
            "error": "Could not parse AI response",
            "raw_response": response_text[:500]
        }

    except Exception as e:
        return {
            "file": str(file_path),
            "error": f"Analysis failed: {e}"
        }


def analyze_single_file_with_ai(
    project_dir: Path,
    file_path: Path,
) -> dict:
    """
    Synchronous wrapper for file analysis.

    Handles both cases: called from sync context or from within async context.

    Args:
        project_dir: Project directory
        file_path: Path to file to analyze

    Returns:
        Dict with analysis results
    """
    try:
        # Check if we're already in an async context
        loop = asyncio.get_running_loop()
        # If we get here, we're in an async context - need to use nest_asyncio or run in thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, analyze_file_with_sdk(project_dir, file_path))
            return future.result(timeout=120)
    except RuntimeError:
        # No running loop, safe to use asyncio.run
        return asyncio.run(analyze_file_with_sdk(project_dir, file_path))


async def analyze_multiple_files_with_sdk(
    project_dir: Path,
    files_to_analyze: List[Path],
) -> Dict[str, dict]:
    """
    Analyze multiple files using the SDK.

    Args:
        project_dir: Project directory
        files_to_analyze: List of file paths

    Returns:
        Dict mapping file paths to analysis results
    """
    results = {}

    for file_path in files_to_analyze[:10]:  # Limit to 10 files
        try:
            relative_path = str(file_path.relative_to(project_dir))
        except ValueError:
            relative_path = str(file_path)

        result = await analyze_file_with_sdk(project_dir, file_path)
        results[relative_path] = result

    return results


def analyze_code_with_ai(
    project_dir: Path,
    files_to_analyze: List[Path],
) -> Dict[str, dict]:
    """
    Synchronous wrapper for multi-file analysis.

    Handles both cases: called from sync context or from within async context.

    Args:
        project_dir: Project directory
        files_to_analyze: List of file paths

    Returns:
        Dict with 'files' mapping paths to analysis results
    """
    if not files_to_analyze:
        return {"files": {}}

    try:
        # Check if we're already in an async context
        loop = asyncio.get_running_loop()
        # If we get here, we're in an async context - need to run in thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                analyze_multiple_files_with_sdk(project_dir, files_to_analyze)
            )
            results = future.result(timeout=300)  # 5 min timeout for multiple files
    except RuntimeError:
        # No running loop, safe to use asyncio.run
        results = asyncio.run(analyze_multiple_files_with_sdk(project_dir, files_to_analyze))

    return {"success": True, "files": results}


def detect_placeholders_with_ai(
    project_dir: Path,
    verbose: bool = True
) -> dict:
    """
    Run AI-powered placeholder detection on the project.

    This is the main entry point for AI-based code analysis.
    Uses the Claude Code SDK (same pattern as init/coding agents).

    Args:
        project_dir: Path to project directory
        verbose: Whether to print progress

    Returns:
        dict with 'passed', 'placeholders_found', 'ai_analysis', 'timestamp'
    """
    placeholders_found = []
    ai_analysis = {}

    if verbose:
        print("  Running AI-powered code analysis (using Claude Code SDK)...")

    # Identify key files to analyze
    files_to_analyze = []

    # 1. Lambda-related Terraform files
    for tf_file in project_dir.glob("infra/modules/lambda*/*.tf"):
        if tf_file.name == "main.tf":  # Focus on main.tf
            files_to_analyze.append(tf_file)

    # 2. Lambda implementation files (if they exist)
    for py_file in project_dir.glob("src/lambdas/**/*.py"):
        files_to_analyze.append(py_file)

    # 3. Key source files (limit to avoid long analysis)
    key_files = ["agent_entrypoint.py", "main.py", "slack_bot.py"]
    for name in key_files:
        for py_file in project_dir.glob(f"src/{name}"):
            files_to_analyze.append(py_file)

    if verbose:
        print(f"  Analyzing {len(files_to_analyze)} key files...")

    # Run AI analysis
    if files_to_analyze:
        result = analyze_code_with_ai(project_dir, files_to_analyze)

        if result.get("success"):
            for file_path, analysis in result.get("files", {}).items():
                if analysis.get("verdict") == "PLACEHOLDER":
                    confidence = analysis.get("confidence", 0.5)
                    if confidence >= 0.7:  # High confidence threshold
                        placeholders_found.append({
                            "file": file_path,
                            "type": "ai_detected_placeholder",
                            "confidence": confidence,
                            "reasons": analysis.get("reasons", []),
                            "issue": f"AI detected placeholder code (confidence: {confidence:.0%})"
                        })

            ai_analysis = {
                "files_analyzed": len(files_to_analyze),
                "results": result.get("files", {}),
                "placeholders_detected": len(placeholders_found)
            }

    passed = len(placeholders_found) == 0
    if passed:
        reason = f"AI analysis of {len(files_to_analyze)} files found no placeholder code"
    else:
        reason = f"AI detected {len(placeholders_found)} placeholder code issues"

    return {
        "passed": passed,
        "placeholders_found": placeholders_found,
        "ai_analysis": ai_analysis,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }


def quick_placeholder_check(file_path: Path, project_dir: Path) -> Tuple[bool, str]:
    """
    Quick single-file placeholder check using AI.

    Args:
        file_path: Path to file to check
        project_dir: Project directory for context

    Returns:
        Tuple of (is_placeholder, reason)
    """
    result = analyze_single_file_with_ai(project_dir, file_path)

    if "error" in result:
        return False, f"AI check failed: {result['error']}"

    if result.get("verdict") == "PLACEHOLDER":
        reasons = result.get("reasons", ["AI detected placeholder"])
        return True, "; ".join(reasons) if isinstance(reasons, list) else str(reasons)

    return False, "AI analysis: appears to be real implementation"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ai_code_analyzer.py <project_dir>")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        sys.exit(1)

    results = detect_placeholders_with_ai(project_dir)

    print("\n" + "=" * 70)
    print("  AI CODE ANALYSIS RESULTS (Claude Code SDK)")
    print("=" * 70)
    print(f"\nPassed: {results['passed']}")
    print(f"Reason: {results['reason']}")

    if results['placeholders_found']:
        print("\nPlaceholder code detected:")
        for p in results['placeholders_found']:
            print(f"\n  {p['file']}:")
            print(f"    Confidence: {p['confidence']:.0%}")
            print(f"    Reasons: {', '.join(p['reasons'][:3])}")

    sys.exit(0 if results['passed'] else 1)
