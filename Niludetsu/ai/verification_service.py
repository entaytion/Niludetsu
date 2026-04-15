import os
import aiohttp
import json
from typing import Dict, Any
from Niludetsu.ai.models import MISTRAL_SMALL_MODEL
from Niludetsu.ai.prompts import VERIFICATION_SYSTEM_PROMPT

class VerificationService:
    """Service to handle AI verification requests using Mistral."""
    
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = MISTRAL_SMALL_MODEL

    async def score_user(self, user_data: Dict[str, Any], answer: str) -> Dict[str, Any]:
        """
        Send user data and answer to LLM for scoring.
        Returns a JSON dictionary with decision and score.
        """
        if not self.api_key:
            # Fail-safe: if no API key, force manual review
            return self._manual_review_fallback("AI API Key Missing")

        prompt = self._construct_prompt(user_data, answer)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": VERIFICATION_SYSTEM_PROMPT
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2, # Low temperature for consistent JSON
            "response_format": {"type": "json_object"}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload, timeout=10) as response:
                    if response.status != 200:
                        return self._manual_review_fallback(f"API Error {response.status}")
                    
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    try:
                        result = json.loads(content)
                        # Validate structure
                        if "score" not in result or "decision" not in result:
                             return self._manual_review_fallback("Invalid JSON Structure")
                        return result
                    except json.JSONDecodeError:
                        return self._manual_review_fallback("JSON Parse Error")

        except Exception as e:
             return self._manual_review_fallback(f"Exception: {str(e)}")

    def _construct_prompt(self, user: Dict[str, Any], answer: str) -> str:
        return f"""
Analyze this verification request for the Discord server 'Æther'.and

User Metadata:
- ID: {user.get('id')}
- Created: {user.get('created_at')}
- Has Avatar: {user.get('has_avatar')}
- Join/Leave Count: {user.get('leave_count', 0)}

User Answer: "{answer}"

SCORING CRITERIA (Max 5):
1. Content (0-2): Meaningful answer? 0=nonsense/too short, 1=ok, 2=good.
2. Logic (0-1): Coherent thought?
3. Tone (0-1): Aggressive/Troll = 0.
4. Naturalness (0-1): Is the text NATURAL? 
   - If it looks like ChatGPT/AI generated (too formal, perfect grammar, "As an AI...", robotic structure) -> SCORE 0 here.
   - If it has human imperfections (slang, lowercase, typos, emojis) -> SCORE 1.

DECISION LOGIC:
- Score >= 4 -> "approve"
- Score 2-3 -> "manual_review"
- Score <= 1 -> "reject"

OUTPUT FORMAT (JSON ONLY):
{{
  "score": <int>,
  "breakdown": {{
    "content": <int>,
    "logic": <int>,
    "tone": <int>,
    "naturalness": <int>
  }},
  "decision": "approve" | "manual_review" | "reject",
  "reason": "<short explanation in Russian>"
}}
"""

    def _manual_review_fallback(self, reason: str) -> Dict[str, Any]:
        return {
            "score": 0,
            "breakdown": {"content": 0, "logic": 0, "tone": 0, "naturalness": 0},
            "decision": "manual_review",
            "reason": f"System Failover: {reason}"
        }
