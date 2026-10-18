from __future__ import annotations

from typing import Any, Dict, List
import re


class NerEntityExtractor:
    """Modular NER extraction engine.
    In V2 prompt-first, extraction is unified via Groq LLM.
    This class maintains compatibility with entity span inspection endpoints.
    """

    def __init__(self, model_name: str = "groq-prompt-first"):
        self.model_name = model_name

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        entities = []
        
        # Phone numbers
        for match in re.finditer(r"(?:\+?91[\-\s]?)?[6-9]\d{9}", text):
            entities.append({
                "entity": "CONTACT",
                "word": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.95
            })

        # Prices
        for match in re.finditer(r"(?:rs\.?|inr|₹|\$)?\s*\d+(?:\.\d+)?\s*(?:rs|rupees|inr|dollars)?", text, re.IGNORECASE):
            entities.append({
                "entity": "PRICE",
                "word": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.92
            })

        return entities
