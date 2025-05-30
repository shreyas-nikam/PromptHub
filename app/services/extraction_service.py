# app/services/extraction_service.py
import PyPDF2
from bs4 import BeautifulSoup
import requests
from typing import List, Dict

class ExtractionService:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def extract_from_url(self, url: str) -> List[Dict]:
        """Extract prompts from a web page"""
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        return await self._extract_prompts_from_text(text, source_type='web', source_url=url)
    
    async def extract_from_pdf(self, pdf_content: bytes) -> List[Dict]:
        """Extract prompts from PDF content"""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return await self._extract_prompts_from_text(text, source_type='pdf')
    
    async def _extract_prompts_from_text(
        self,
        text: str,
        source_type: str,
        source_url: Optional[str] = None
    ) -> List[Dict]:
        """Use LLM to identify and extract prompts from text"""
        extraction_prompt = """
        Analyze the following text and extract any prompts or prompt templates.
        
        Text: {text}
        
        For each prompt found, extract:
        1. The prompt content
        2. A suggested name
        3. A description of its purpose
        4. Any mentioned required fields or parameters
        5. The context in which it's used
        
        Return as JSON array: [
            {{
                "content": "prompt text",
                "name": "suggested name",
                "description": "what it does",
                "required_fields": ["field1", "field2"],
                "context": "usage context"
            }}
        ]
        """
        
        result = await self.llm_service.generate(
            extraction_prompt.format(text=text[:4000]),  # Limit text length
            model="gpt-4",
            response_format={"type": "json_object"}
        )
        
        prompts = []
        for extracted in result:
            prompts.append({
                **extracted,
                'source_type': source_type,
                'source_url': source_url,
                'extracted_by': 'gpt-4',
                'extraction_metadata': {
                    'text_length': len(text),
                    'extraction_date': datetime.utcnow().isoformat()
                }
            })
        
        return prompts