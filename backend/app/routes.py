from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from groq import Groq
import json

router = APIRouter()

# =========================
# Validate API key
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set in environment")

client = Groq(api_key=api_key)

# =========================
# Models
# =========================

class CodeReviewRequest(BaseModel):
    code: str
    language: str
    focus_areas: Optional[List[str]] = None


class ReviewIssue(BaseModel):
    line: Optional[int]
    severity: str
    description: str
    fix: str


class CodeReviewResponse(BaseModel):
    summary: str
    issues: List[ReviewIssue]


class CodeRewriteRequest(BaseModel):
    code: str
    language: str
    instructions: Optional[str] = "Improve code quality"


class CodeRewriteResponse(BaseModel):
    rewritten_code: str
    explanation: str
    improvements: List[str]


class ExplainResponse(BaseModel):
    explanation: str
    steps: List[str]
    key_concepts: List[str]

# =========================
# Helper: Safe LLM Call
# =========================

def call_llm(system_prompt: str, user_prompt: str):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = completion.choices[0].message.content
        return json.loads(content)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON from model: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM error: {str(e)}"
        )

# =========================
# Route 1: Review Code
# =========================

@router.post("/review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    focus = request.focus_areas or []
    focus_str = ", ".join(focus)

    system_prompt = """
You are a senior code reviewer.
Return ONLY valid JSON with this schema:
{
  "summary": "string",
  "issues": [
    {
      "line": number or null,
      "severity": "critical|high|medium|low",
      "description": "string",
      "fix": "string"
    }
  ]
}
"""

    user_prompt = f"""
Language: {request.language}
Focus Areas: {focus_str}

Code:
{request.code}
"""

    data = call_llm(system_prompt, user_prompt)
    return data

# =========================
# Route 2: Rewrite Code
# =========================

@router.post("/rewrite", response_model=CodeRewriteResponse)
async def rewrite_code(request: CodeRewriteRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    system_prompt = """
You are an expert software engineer.
Return ONLY JSON:
{
  "rewritten_code": "string",
  "explanation": "string",
  "improvements": ["string"]
}
"""

    user_prompt = f"""
Language: {request.language}
Instructions: {request.instructions}

Code:
{request.code}
"""

    data = call_llm(system_prompt, user_prompt)
    return data

# =========================
# Route 3: Explain Code
# =========================

@router.post("/explain", response_model=ExplainResponse)
async def explain_code(request: Dict[str, Any]):
    code = request.get("code", "")
    language = request.get("language", "")

    if not code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    system_prompt = """
You are a programming teacher.
Return ONLY JSON:
{
  "explanation": "string",
  "steps": ["string"],
  "key_concepts": ["string"]
}
"""

    user_prompt = f"""
Explain this {language} code:

{code}
"""

    data = call_llm(system_prompt, user_prompt)
    return data