import logging
from typing import Dict, Any

log = logging.getLogger("Zia.nlp")

_nlp = None

def get_spacy_model():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except ImportError:
            log.warning("Spacy or en_core_web_sm not installed. Fallback to basic NLP.")
            _nlp = "fallback"
        except OSError:
            log.warning("Spacy model en_core_web_sm not found. Fallback to basic NLP.")
            _nlp = "fallback"
    return _nlp

def extract_intent_entities(text: str) -> Dict[str, Any]:
    """
    Extracts the subject (entities) and the root intent from the text using spaCy.
    Returns a dictionary of parsed info.
    """
    nlp = get_spacy_model()
    
    if nlp == "fallback" or nlp is None:
        return {"intent": "unknown", "entities": []}
        
    doc = nlp(text)
    
    intent = "unknown"
    entities = []
    
    for token in doc:
        if token.dep_ == "ROOT":
            intent = token.lemma_
    
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_})
        
    if not entities:
        # Fallback to noun chunks if no named entities found
        for chunk in doc.noun_chunks:
            # Avoid picking up pronouns like "I" or "it" as primary entities unless nothing else exists
            if chunk.root.pos_ != "PRON":
                entities.append({"text": chunk.text, "label": "NOUN_CHUNK"})
                
    return {
        "intent": intent,
        "entities": entities
    }

def format_parsed_context(parsed: Dict[str, Any]) -> str:
    """Formats the extracted NLP data into a string for the LLM context."""
    if parsed["intent"] == "unknown" and not parsed["entities"]:
        return ""
        
    ent_str = ", ".join([f"{e['text']} ({e['label']})" for e in parsed["entities"]])
    return f"\n[System NLP Analysis] Intent Root: {parsed['intent'].upper()} | Extracted Subjects: {ent_str}"
