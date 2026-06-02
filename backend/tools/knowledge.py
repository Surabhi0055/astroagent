import json
import os

def lookup_astrology_meaning(query: str) -> str:
    """
    Looks up spiritual astrology meanings from our curated database.
    Query should be the planet and sign, e.g., 'Sun in Aquarius' or 'Moon in Gemini'.
    """
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "astrology_knowledge.json")
    
    try:
        with open(file_path, "r") as f:
            knowledge_base = json.load(f)
    except FileNotFoundError:
        return "Knowledge base file not found."

    for key, meaning in knowledge_base.items():
        if key.lower() in query.lower():
            return f"Curated Meaning for {key}: {meaning}"
            
    return "No curated knowledge found for this query. Provide a warm, general interpretation."

if __name__ == "__main__":
    print(lookup_astrology_meaning("Sun in Aquarius"))
