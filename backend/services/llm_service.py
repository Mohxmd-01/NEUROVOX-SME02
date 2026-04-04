"""
Central LLM service — Uses Google Gemini API as primary, Groq as fallback.
All agents call through this single wrapper.
"""
import json
import google.generativeai as genai
from openai import OpenAI
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import GEMINI_API_KEY, GROQ_API_KEY, LLM_MODEL, GROQ_MODEL

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configure Groq (OpenAI-compatible)
groq_client = None
if GROQ_API_KEY:
    groq_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )


def call_llm(system_prompt: str, user_prompt: str, json_mode: bool = True) -> dict | str:
    """Central LLM call — tries Gemini first, falls back to Groq"""
    
    # Try Gemini first
    if GEMINI_API_KEY:
        try:
            return _call_gemini(system_prompt, user_prompt, json_mode)
        except Exception as e:
            print(f"⚠️ Gemini failed: {e}, trying Groq fallback...")
    
    # Try Groq fallback
    if groq_client:
        try:
            return _call_groq(system_prompt, user_prompt, json_mode)
        except Exception as e:
            print(f"⚠️ Groq also failed: {e}")
    
    # Return error
    if json_mode:
        return {"error": "All LLM providers failed"}
    return "LLM service unavailable"


def _call_gemini(system_prompt: str, user_prompt: str, json_mode: bool) -> dict | str:
    """Call Google Gemini API"""
    model = genai.GenerativeModel(
        model_name=LLM_MODEL,
        system_instruction=system_prompt
    )
    
    generation_config = {
        "temperature": 0.3,
        "max_output_tokens": 4000,
    }
    
    if json_mode:
        generation_config["response_mime_type"] = "application/json"
    
    response = model.generate_content(
        user_prompt,
        generation_config=generation_config
    )
    
    content = response.text.strip()
    
    if json_mode:
        # Clean any markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
    
    return content


def _call_groq(system_prompt: str, user_prompt: str, json_mode: bool) -> dict | str:
    """Call Groq API (OpenAI-compatible)"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    kwargs = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4000
    }
    
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    
    response = groq_client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content.strip()
    
    if json_mode:
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
    
    return content


def call_llm_with_context(system_prompt: str, user_prompt: str, context: str, json_mode: bool = False) -> str:
    """LLM call with RAG context injected"""
    enhanced_prompt = f"""
COMPANY KNOWLEDGE CONTEXT:
{context}

USER REQUEST:
{user_prompt}
"""
    return call_llm(system_prompt, enhanced_prompt, json_mode=json_mode)
