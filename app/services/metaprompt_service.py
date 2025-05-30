# app/services/metaprompt_service.py
class MetapromptService:
    def __init__(self):
        self.llm_service = LLMService()
        self.templates = self._load_metaprompt_templates()
    
    async def enhance_prompt(
        self,
        original_prompt: str,
        context: Dict,
        template_name: Optional[str] = None
    ) -> str:
        """
        Enhances a prompt using metaprompting techniques
        """
        template = self.templates.get(template_name, self.templates['default'])
        
        metaprompt = template.format(
            original_prompt=original_prompt,
            context=json.dumps(context, indent=2)
        )
        
        enhanced = await self.llm_service.generate(
            metaprompt,
            model="gpt-4",
            temperature=0.7
        )
        
        return enhanced
    
    def _load_metaprompt_templates(self) -> Dict[str, str]:
        return {
            'default': """
            You are an expert prompt engineer. Enhance the following prompt to be more effective.
            
            Original Prompt: {original_prompt}
            Context: {context}
            
            Guidelines:
            1. Make the prompt clear and specific
            2. Include examples where helpful
            3. Define the expected output format
            4. Add constraints and guidelines
            5. Ensure the prompt is complete and self-contained
            
            Enhanced Prompt:
            """,
            'technical': """
            Transform this technical prompt into a comprehensive, well-structured prompt.
            
            Original: {original_prompt}
            Context: {context}
            
            Include:
            - Clear problem statement
            - Technical requirements
            - Expected input/output formats
            - Edge cases to consider
            - Performance considerations
            
            Enhanced Technical Prompt:
            """
        }