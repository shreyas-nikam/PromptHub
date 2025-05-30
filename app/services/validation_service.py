# app/services/validation_service.py
from typing import Dict, List, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.services.llm_service import LLMService

class ValidationService:
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm_service = LLMService()
    
    async def validate_pre_invocation(
        self,
        user_prompt: str,
        system_prompt: str,
        metaprompt_output: str,
        validation_config: Dict
    ) -> Tuple[bool, float, str]:
        """
        Validates prompt before execution using both embedding distance
        and LLM critique
        """
        # Design 1: Embedding-based validation
        embedding_score = await self._validate_by_embeddings(
            user_prompt, system_prompt, metaprompt_output
        )
        
        # Design 2: LLM-based critique
        llm_score, critique = await self._validate_by_llm_critique(
            user_prompt, system_prompt, metaprompt_output
        )
        
        # Combined validation
        final_score = (embedding_score * 0.4 + llm_score * 0.6)
        is_valid = final_score >= validation_config.get('threshold', 0.7)
        
        return is_valid, final_score, critique
    
    async def _validate_by_embeddings(
        self,
        user_prompt: str,
        system_prompt: str,
        metaprompt_output: str
    ) -> float:
        # Compute embeddings
        combined_input = f"{system_prompt}\n{user_prompt}"
        input_embedding = self.embedder.encode(combined_input)
        output_embedding = self.embedder.encode(metaprompt_output)
        
        # Calculate cosine similarity
        similarity = np.dot(input_embedding, output_embedding) / (
            np.linalg.norm(input_embedding) * np.linalg.norm(output_embedding)
        )
        
        return similarity
    
    async def _validate_by_llm_critique(
        self,
        user_prompt: str,
        system_prompt: str,
        metaprompt_output: str
    ) -> Tuple[float, str]:
        critique_prompt = f"""
        Evaluate the completeness and thoroughness of the generated prompt.
        
        Original User Prompt: {user_prompt}
        System Prompt: {system_prompt}
        Generated Meta Prompt: {metaprompt_output}
        
        Score from 0-1 based on:
        1. Completeness - Does it capture all requirements?
        2. Clarity - Is it clear and unambiguous?
        3. Thoroughness - Does it provide sufficient detail?
        4. Alignment - Does it align with the system prompt?
        
        Return JSON: {{"score": float, "critique": "detailed feedback"}}
        """
        
        result = await self.llm_service.generate(
            critique_prompt,
            model="gpt-4",
            response_format={"type": "json_object"}
        )
        
        return result['score'], result['critique']
    
    
    # app/services/validation_service.py (continued)
    async def validate_post_invocation(
        self,
        prompt: str,
        output: str,
        expected_format: Dict,
        guardrail_config: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Validates LLM output against guardrails and expected format
        """
        issues = []
        
        # Format validation
        if not self._validate_format(output, expected_format):
            issues.append("Output format does not match expected structure")
        
        # Content validation
        content_issues = await self._validate_content(output, guardrail_config)
        issues.extend(content_issues)
        
        # Safety validation
        safety_issues = await self._validate_safety(output)
        issues.extend(safety_issues)
        
        is_valid = len(issues) == 0
        return is_valid, issues

    async def _validate_content(self, output: str, config: Dict) -> List[str]:
        """Check for prohibited content, required elements, etc."""
        issues = []
        
        # Check prohibited terms
        if prohibited := config.get('prohibited_terms'):
            for term in prohibited:
                if term.lower() in output.lower():
                    issues.append(f"Prohibited term found: {term}")
        
        # Check required elements
        if required := config.get('required_elements'):
            for element in required:
                if element not in output:
                    issues.append(f"Required element missing: {element}")
        
        return issues