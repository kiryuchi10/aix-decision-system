"""
DeepSeek AI Service for Chat Integration
Provides LLM capabilities for the AiX Decision System chat feature.
"""
import os
import httpx
from typing import List, Dict, Optional
from app.core.config import settings

class DeepSeekService:
    """Service for interacting with DeepSeek API"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = 30.0
        
    def is_configured(self) -> bool:
        """Check if DeepSeek API is configured"""
        return bool(self.api_key)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Send chat request to DeepSeek API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text from the model
        """
        if not self.is_configured():
            raise ValueError("DeepSeek API key not configured. Set DEEPSEEK_API_KEY environment variable.")
        
        # Prepare messages
        api_messages = []
        if system_prompt:
            api_messages.append({
                "role": "system",
                "content": system_prompt
            })
        api_messages.extend(messages)
        
        # Prepare request
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Make request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract response text
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    raise ValueError("Unexpected response format from DeepSeek API")
                    
            except httpx.HTTPStatusError as e:
                error_msg = f"DeepSeek API error: {e.response.status_code}"
                if e.response.text:
                    error_msg += f" - {e.response.text}"
                raise ValueError(error_msg)
            except httpx.RequestError as e:
                raise ValueError(f"Failed to connect to DeepSeek API: {str(e)}")
    
    def get_system_prompt_for_aix(self) -> str:
        """Get system prompt for AiX Decision System context"""
        return """You are an AI assistant for the AiX Decision System, a semiconductor manufacturing process control and optimization platform.

Your role is to help users:
1. Understand process data, SPC metrics, FDC alarms, and recommendations
2. Query and analyze data from the database
3. Interpret control charts, drift detection, and capability metrics
4. Provide insights on process optimization and troubleshooting

Database Schema Overview:
- users: System users
- papers: Research papers uploaded
- datasets: Process datasets (CSV files)
- seed_catalog: Seed data templates
- synthetic_runs: Generated synthetic data
- spc_metrics: Statistical Process Control metrics
- spc_rule_violations: SPC rule violations
- coupling_actions: Coupling control actions
- alarms: FDC alarms
- recommendations: AI-generated recommendations
- experiments: DoE experiments
- recipes: Process recipes
- sensor_data: Time-series sensor readings

When answering questions:
- Be concise and technical but clear
- Reference specific tables/columns when discussing data
- Suggest relevant queries or analyses
- Provide actionable insights
- If you don't know something, say so rather than guessing

Always respond in a helpful, professional manner."""

# Global instance
deepseek_service = DeepSeekService()
