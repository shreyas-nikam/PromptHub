# app/services/llm_service.py
from typing import Dict, List, Any
import asyncio
import time
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

class LLMService:
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        self.anthropic_client = AsyncAnthropic()
        self.model_configs = {
            'openai': {
                'gpt-4': {'max_tokens': 4096, 'default_temp': 0.7},
                'gpt-3.5-turbo': {'max_tokens': 4096, 'default_temp': 0.7}
            },
            'anthropic': {
                'claude-3-opus': {'max_tokens': 4096, 'default_temp': 0.7},
                'claude-3-sonnet': {'max_tokens': 4096, 'default_temp': 0.7}
            }
        }
    
    async def compare_models(
        self,
        prompt: str,
        models: List[Dict[str, str]],
        input_data: Dict
    ) -> Dict[str, Any]:
        """Execute prompt across multiple models for comparison"""
        tasks = []
        for model_config in models:
            task = self.execute_single(
                prompt,
                model_config['provider'],
                model_config['name'],
                input_data
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        comparison = {}
        for i, result in enumerate(results):
            model_key = f"{models[i]['provider']}_{models[i]['name']}"
            if isinstance(result, Exception):
                comparison[model_key] = {
                    'error': str(result),
                    'status': 'failed'
                }
            else:
                comparison[model_key] = result
        
        return comparison
    
    async def execute_single(
        self,
        prompt: str,
        provider: str,
        model: str,
        input_data: Dict,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute prompt on a single model"""
        start_time = time.time()
        
        try:
            formatted_prompt = prompt.format(**input_data)
            
            if provider == 'openai':
                response = await self._execute_openai(formatted_prompt, model, **kwargs)
            elif provider == 'anthropic':
                response = await self._execute_anthropic(formatted_prompt, model, **kwargs)
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            latency = int((time.time() - start_time) * 1000)
            
            return {
                'output': response['content'],
                'latency_ms': latency,
                'token_count': response.get('token_count', 0),
                'cost_usd': self._calculate_cost(provider, model, response.get('token_count', 0)),
                'status': 'success',
                'metadata': response.get('metadata', {})
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'latency_ms': int((time.time() - start_time) * 1000),
                'status': 'failed'
            }
    
    async def _execute_openai(self, prompt: str, model: str, **kwargs) -> Dict:
        """Execute on OpenAI models"""
        messages = []
        if system_prompt := kwargs.get('system_prompt'):
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            top_p=kwargs.get('top_p', 1.0),
            frequency_penalty=kwargs.get('frequency_penalty', 0),
            presence_penalty=kwargs.get('presence_penalty', 0)
        )
        
        return {
            'content': response.choices[0].message.content,
            'token_count': response.usage.total_tokens,
            'metadata': {
                'finish_reason': response.choices[0].finish_reason,
                'model': response.model
            }
        }
    
    async def _execute_anthropic(self, prompt: str, model: str, **kwargs) -> Dict:
        """Execute on Anthropic models"""
        system = kwargs.get('system_prompt', '')
        
        response = await self.anthropic_client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            system=system,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000)
        )
        
        return {
            'content': response.content[0].text,
            'token_count': response.usage.input_tokens + response.usage.output_tokens,
            'metadata': {
                'stop_reason': response.stop_reason,
                'model': response.model
            }
        }
    
    def _calculate_cost(self, provider: str, model: str, tokens: int) -> float:
        """Calculate cost based on token usage"""
        # Simplified cost calculation - should be updated with actual pricing
        cost_per_1k = {
            'openai': {
                'gpt-4': 0.03,
                'gpt-3.5-turbo': 0.002
            },
            'anthropic': {
                'claude-3-opus': 0.015,
                'claude-3-sonnet': 0.003
            }
        }
        
        rate = cost_per_1k.get(provider, {}).get(model, 0.01)
        return (tokens / 1000) * rate