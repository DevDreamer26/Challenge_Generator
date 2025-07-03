import os
import json
import google.generativeai as genai 
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def generate_challenge_with_ai(difficulty: str) -> Dict[str, Any]:
    
    model = genai.GenerativeModel('gemini-2.5-flash') 

    system_prompt = f"""You are an expert coding challenge creator. 
    Your task is to generate a coding question with multiple choice answers.
    The question should be appropriate for the specified difficulty level.

    For easy questions: Focus on basic syntax, simple operations, or common programming concepts.
    For medium questions: Cover intermediate concepts like data structures, algorithms, or language features.
    For hard questions: Include advanced topics, design patterns, optimization techniques, or complex algorithms.

    Return the challenge strictly in the following JSON structure. Ensure the output is a valid JSON object, and only the JSON:
    ```json
    {{
        "title": "The question title",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_answer_id": 0, // Index of the correct answer (0-3)
        "explanation": "Detailed explanation of why the correct answer is right"
    }}
    ```
    Make sure the options are plausible but with only one clearly correct answer.
    """
    try:
        
        response = model.generate_content(
            [
                {"role": "user", "parts": [system_prompt]},
                {"role": "model", "parts": ["Understood. I will provide challenges in the specified JSON format."]}, 
                {"role": "user", "parts": [f"Generate a {difficulty} difficulty coding challenge."]}
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                
            )
        )

        
        content = response.text
        
        if content.startswith("```json") and content.endswith("```"):
            content = content[len("```json"):len(content)-len("```")].strip()

        challenge_data = json.loads(content)

        required_fields = ["title", "options", "correct_answer_id", "explanation"]
        for field in required_fields:
            if field not in challenge_data:
                raise ValueError(f"Missing required field: {field} in generated JSON: {challenge_data}")

        
        if not isinstance(challenge_data.get("options"), list) or len(challenge_data["options"]) != 4:
            raise ValueError("Options must be a list of exactly 4 elements.")
        if not (0 <= challenge_data.get("correct_answer_id", -1) <= 3):
            raise ValueError("correct_answer_id must be between 0 and 3.")

        return challenge_data

    except Exception as e:
        print(f"AI generation error: {e}")
        
        return {
            "title": "Basic Python List Operation",
            "options": [
                "my_list.append(5)",
                "my_list.add(5)",
                "my_list.push(5)",
                "my_list.insert(5)",
            ],
            "correct_answer_id": 0,
            "explanation": "In Python, append() is the correct method to add an element to the end of a list."
        }
        
