import json
import os
import re

def lookup_astrology_meaning(query: str) -> str:
    """
    Looks up spiritual astrology meanings from our curated database using a term frequency ranking algorithm.
    Returns the top 2 most relevant knowledge chunks to provide maximum context while saving tokens.
    """
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "astrology_knowledge.json")
    
    try:
        with open(file_path, "r") as f:
            knowledge_base = json.load(f)
    except FileNotFoundError:
        return "Knowledge base file not found."

    # Normalize query into a set of words
    query_words = set(re.findall(r'\w+', query.lower()))
    if not query_words:
        return "No curated knowledge found for this query."

    scored_chunks = []
    
    for key, meaning in knowledge_base.items():
        # Score based on exact key match first
        score = 0
        key_lower = key.lower()
        if key_lower in query.lower():
            score += 100
            
        # Then score based on word overlap between query and the key/meaning
        chunk_text = (key_lower + " " + meaning.lower())
        chunk_words = set(re.findall(r'\w+', chunk_text))
        
        # Calculate Jaccard-like similarity
        overlap = query_words.intersection(chunk_words)
        score += len(overlap) * 10
        
        if score > 0:
            scored_chunks.append((score, key, meaning))

    if not scored_chunks:
        return "No curated knowledge found for this query. Provide a warm, general interpretation."

    # Sort by score descending and take top 2
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = scored_chunks[:2]
    
    result = "CURATED ASTROLOGY KNOWLEDGE:\n"
    for _, key, meaning in top_chunks:
        result += f"- {key}: {meaning}\n"
        
    return result

if __name__ == "__main__":
    print(lookup_astrology_meaning("Tell me about my Gemini moon"))
