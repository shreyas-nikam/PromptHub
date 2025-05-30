# app/services/webhook_service.py
from typing import List, Dict, Any
import httpx
from app.models.webhook import Webhook
from app.models.prompt import PromptVersion
import asyncio
from datetime import datetime

class WebhookService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def trigger_prompt_update(
        self,
        prompt_version: PromptVersion,
        event_type: str = "prompt.updated"
    ):
        """Trigger webhooks for prompt update"""
        # Get all webhooks for the application
        webhooks = await Webhook.find(
            Webhook.application_id == prompt_version.application_id,
            Webhook.is_active == True,
            Webhook.events == event_type
        ).to_list()
        
        tasks = []
        for webhook in webhooks:
            task = self._send_webhook(webhook, {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "prompt_id": str(prompt_version.prompt_id),
                    "version": prompt_version.version,
                    "content": prompt_version.content,
                    "is_published": prompt_version.is_published
                }
            })
            tasks.append(task)
        
        # Send all webhooks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                await self._log_webhook_failure(webhooks[i], str(result))
    
    async def _send_webhook(self, webhook: Webhook, payload: Dict[str, Any]):
        """Send individual webhook"""
        headers = {
            "Content-Type": "application/json",
            "X-PromptHub-Signature": self._generate_signature(
                payload, webhook.secret
            )
        }
        
        response = await self.client.post(
            webhook.url,
            json=payload,
            headers=headers
        )
        
        response.raise_for_status()
        
        # Update last triggered
        webhook.last_triggered = datetime.utcnow()
        await webhook.save()
    
    def _generate_signature(self, payload: Dict, secret: str) -> str:
        """Generate HMAC signature for webhook"""
        import hmac
        import hashlib
        import json
        
        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"