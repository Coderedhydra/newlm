from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from rich.console import Console

console = Console()


class GeminiClient:
    """Thin wrapper around google-generativeai for JSON responses.

    Falls back from the requested model to a sensible default if unavailable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        fallback_model_name: str = "gemini-1.5-flash-latest",
    ) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY not set. Export it or pass api_key to GeminiClient."
            )
        self.model_name = model_name
        self.fallback_model_name = fallback_model_name
        # Lazy import to avoid dependency cost if not used
        try:
            from google import generativeai as genai  # type: ignore
        except Exception as exc:  # pragma: no cover - import-time failure
            raise RuntimeError(
                "google-generativeai is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self._genai = genai
        self._genai.configure(api_key=self.api_key)

    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """Generate strictly-JSON content from the model.

        Returns parsed JSON as a Python dict.
        """
        model = self._get_model(self.model_name, system_instruction)
        try:
            response = model.generate_content(
                [prompt],
                generation_config={
                    "response_mime_type": "application/json",
                },
            )
            return json.loads(response.text)
        except Exception as primary_error:
            console.print(
                f"[yellow]Primary model '{self.model_name}' failed, trying fallback '{self.fallback_model_name}'.[/yellow]"
            )
            model = self._get_model(self.fallback_model_name, system_instruction)
            try:
                response = model.generate_content(
                    [prompt],
                    generation_config={
                        "response_mime_type": "application/json",
                    },
                )
                return json.loads(response.text)
            except Exception as fallback_error:
                raise RuntimeError(
                    f"Gemini generation failed: {primary_error}\nFallback error: {fallback_error}"
                )

    def _get_model(self, model_name: str, system_instruction: Optional[str]):
        return self._genai.GenerativeModel(
            model_name,
            system_instruction=system_instruction,
        )

