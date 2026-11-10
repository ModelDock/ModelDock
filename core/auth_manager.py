"""
ModelDock Studio - Hugging Face Authentication Manager
Validates HF access tokens, fetches user profile & permissions, and manages gated model credentials.
"""

from typing import Dict, Any, Optional
import httpx
from core.config import ConfigManager

HF_WHOAMI_URL = "https://huggingface.co/api/whoami-v2"


class AuthManager:
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager.get_instance()

    def get_token(self) -> str:
        return self.config.get("hf_token", "").strip()

    def get_auth_headers(self) -> Dict[str, str]:
        token = self.get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a Hugging Face token against the official HF Hub API.
        Returns user info and permissions if valid, or raises an informative error.
        """
        cleaned_token = token.strip()
        if not cleaned_token:
            return {
                "valid": False,
                "error": "Token is empty. Please enter a valid Hugging Face Access Token (starting with 'hf_').",
            }

        headers = {
            "Authorization": f"Bearer {cleaned_token}",
            "User-Agent": "ModelDock-Studio/1.0",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(HF_WHOAMI_URL, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    user_profile = {
                        "valid": True,
                        "username": data.get("name", "Unknown"),
                        "fullname": data.get("fullname", ""),
                        "email": data.get("email", ""),
                        "avatar_url": data.get("avatarUrl", ""),
                        "orgs": [org.get("name") for org in data.get("orgs", [])],
                        "can_pay": data.get("canPay", False),
                        "token_role": (data.get("auth", {}).get("accessToken", {}) or {}).get("role", "read"),
                        "token_preview": f"{cleaned_token[:4]}...{cleaned_token[-4:]}" if len(cleaned_token) > 8 else "***",
                    }
                    # Save verified token and profile
                    self.config.set("hf_token", cleaned_token)
                    self.config.set("hf_user", user_profile)
                    return user_profile
                elif res.status_code == 401:
                    return {
                        "valid": False,
                        "error": "Invalid or expired Hugging Face token. Please generate a new User Access Token in your Hugging Face settings.",
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"Hugging Face API returned status {res.status_code}: {res.text}",
                    }
        except httpx.RequestError as e:
            return {
                "valid": False,
                "error": f"Network error connecting to Hugging Face API: {str(e)}",
            }

    async def get_current_auth_status(self) -> Dict[str, Any]:
        """Check current authentication status (cached or re-verified)."""
        token = self.get_token()
        if not token:
            return {
                "authenticated": False,
                "user": None,
                "message": "No Hugging Face token configured (running in Guest / Public mode).",
            }

        cached_user = self.config.get("hf_user")
        if cached_user and cached_user.get("valid"):
            return {
                "authenticated": True,
                "user": cached_user,
                "message": f"Authenticated as @{cached_user.get('username')}",
            }

        # Otherwise re-verify
        res = await self.verify_token(token)
        if res.get("valid"):
            return {
                "authenticated": True,
                "user": res,
                "message": f"Authenticated as @{res.get('username')}",
            }
        else:
            return {
                "authenticated": False,
                "user": None,
                "error": res.get("error"),
                "message": "Configured token is invalid or expired.",
            }

    def logout(self) -> None:
        """Clear the Hugging Face token and user session."""
        self.config.set("hf_token", "")
        self.config.set("hf_user", None)
