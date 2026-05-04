#!/usr/bin/env python3
"""
API Request/Response Capture Module

Captures all API interactions with LLMs for fine-tuning dataset generation.
Logs conversations in a format suitable for fine-tuning open source models.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class APICapture:
    """Captures API requests and responses for fine-tuning datasets."""
    
    def __init__(self, output_file: str = "api_interactions.jsonl"):
        self.output_file = Path(output_file)
        self.interactions = []
        self.request_counter = 0
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for API captures."""
        self.logger = logging.getLogger("api_capture")
        
        # Create file handler
        handler = logging.FileHandler(f"api_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
    
    def capture_request(self, provider: str, model: str, system_prompt: str, user_message: str, metadata: dict = None):
        """Capture a request to an LLM API."""
        request_id = self.request_counter
        self.request_counter += 1
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "request_id": request_id,
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "user_message": user_message,
            "metadata": metadata or {},
        }
        self.interactions.append(interaction)
        self.logger.debug(f"Captured request to {provider}/{model}")
        return request_id
    
    def capture_response(self, request_id: int, response: str, finish_reason: str = "stop", usage: dict = None):
        """Capture a response from an LLM API."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "request_id": request_id,
            "response": response,
            "finish_reason": finish_reason,
            "usage": usage or {},
        }
        self.interactions.append(interaction)
        self.logger.debug(f"Captured response for request {request_id}")
    
    def capture_structured_response(self, request_id: int, structured_data: dict, raw_response: str):
        """Capture a structured (JSON) response from an LLM."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": "structured_response",
            "request_id": request_id,
            "parsed_data": structured_data,
            "raw_response": raw_response,
        }
        self.interactions.append(interaction)
        self.logger.debug(f"Captured structured response for request {request_id}")
    
    def save_interactions(self, output_file: Optional[str] = None):
        """Save all interactions to file."""
        output = Path(output_file or self.output_file)
        with open(output, 'w') as f:
            for interaction in self.interactions:
                f.write(json.dumps(interaction) + '\n')
        logger.info(f"Saved {len(self.interactions)} API interactions to {output}")
    
    def generate_fine_tuning_dataset(self, output_file: str = "fine_tuning_dataset.jsonl"):
        """
        Generate a fine-tuning dataset from captured interactions.
        Format: {"messages": [{"role": "system/user/assistant", "content": "..."}, ...]}
        """
        dataset = []
        request_map = {}
        request_counter = 0
        
        for interaction in self.interactions:
            if interaction["type"] == "request":
                request_map[interaction.get("_request_id", request_counter)] = {
                    "provider": interaction["provider"],
                    "model": interaction["model"],
                    "system": interaction["system_prompt"],
                    "user": interaction["user_message"],
                }
                request_counter += 1
            
            elif interaction["type"] == "response":
                req_id = interaction.get("request_id")
                if req_id is not None and req_id in request_map:
                    req = request_map[req_id]
                    dataset_entry = {
                        "messages": [
                            {"role": "system", "content": req["system"]},
                            {"role": "user", "content": req["user"]},
                            {"role": "assistant", "content": interaction["response"]},
                        ],
                        "metadata": {
                            "provider": req["provider"],
                            "model": req["model"],
                        }
                    }
                    dataset.append(dataset_entry)
        
        # Save dataset
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            for entry in dataset:
                f.write(json.dumps(entry) + '\n')
        
        logger.info(f"Generated fine-tuning dataset with {len(dataset)} examples to {output_path}")
        return output_path


# Global capture instance
_capture_instance: Optional[APICapture] = None


def get_api_capture() -> APICapture:
    """Get or create the global API capture instance."""
    global _capture_instance
    if _capture_instance is None:
        _capture_instance = APICapture()
    return _capture_instance


def init_api_capture(output_file: str = "api_interactions.jsonl") -> APICapture:
    """Initialize the API capture with a specific output file."""
    global _capture_instance
    _capture_instance = APICapture(output_file)
    return _capture_instance
