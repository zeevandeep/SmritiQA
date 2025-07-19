"""
Text processing utilities for improving readability of transcribed journal entries.

This module provides functions for formatting continuous speech-to-text output
into well-structured, readable paragraphs.
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def add_paragraph_breaks(text: str, language: str = 'en') -> str:
    """
    Add logical paragraph breaks to continuous transcribed text.
    
    Uses natural language patterns to identify sentence groupings that should
    be formatted as separate paragraphs for improved readability.
    
    Args:
        text: Continuous text from speech-to-text transcription
        
    Returns:
        Text formatted with paragraph breaks (\n\n between paragraphs)
    """
    if not text or not text.strip():
        return text
    
    # Clean up the text first
    text = text.strip()
    
    # Split into sentences using common sentence endings and also commas for speech patterns
    sentence_pattern = r'([.!?]+)\s+'
    sentences = re.split(sentence_pattern, text)
    
    # Reconstruct sentences with their punctuation
    reconstructed_sentences = []
    for i in range(0, len(sentences), 2):
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]
        else:
            sentence = sentences[i]
        
        sentence = sentence.strip()
        if sentence:
            reconstructed_sentences.append(sentence)
    
    if not reconstructed_sentences:
        return text
    
    # Group sentences into logical paragraphs
    paragraphs = []
    current_paragraph = []
    
    # Get language-specific transition patterns
    new_paragraph_indicators = get_language_patterns(language)
    
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in new_paragraph_indicators]
    
    for i, sentence in enumerate(reconstructed_sentences):
        current_paragraph.append(sentence)
        
        # Determine if we should start a new paragraph
        should_break = False
        
        # First check if next sentence starts with transition words (priority over length)
        if i + 1 < len(reconstructed_sentences):
            next_sentence = reconstructed_sentences[i + 1]
            for pattern in compiled_patterns:
                if pattern.search(next_sentence):
                    should_break = True
                    break
        
        # Only use length as fallback for very long paragraphs (4+ sentences)
        if not should_break and len(current_paragraph) >= 4:
            should_break = True
        
        # Add paragraph break if needed
        if should_break or i == len(reconstructed_sentences) - 1:
            paragraph_text = ' '.join(current_paragraph)
            paragraphs.append(paragraph_text)
            current_paragraph = []
    
    # Handle any remaining sentences
    if current_paragraph:
        paragraph_text = ' '.join(current_paragraph)
        paragraphs.append(paragraph_text)
    
    # Join paragraphs with double line breaks
    formatted_text = '\n\n'.join(paragraphs)
    
    logger.info(f"Formatted text into {len(paragraphs)} paragraphs (original: {len(text)} chars, formatted: {len(formatted_text)} chars)")
    logger.debug(f"Paragraph lengths: {[len(p.split('.')) for p in paragraphs]} sentences each")
    
    return formatted_text


def get_language_patterns(language: str = 'en') -> list:
    """
    Get transition word patterns for different languages.
    
    Args:
        language: Language code (en, hi, es, fr, de, ja, ar, etc.)
        
    Returns:
        List of regex patterns for transition words in the specified language
    """
    patterns = {
        'en': [
            # Topic transition words
            r'\b(anyway|however|meanwhile|additionally|furthermore|moreover|besides|also|next|then|afterwards|later|finally|lastly|in conclusion|to summarize)\b',
            # Time transitions
            r'\b(today|yesterday|tomorrow|this morning|this afternoon|this evening|last week|next week|recently|earlier|afterwards|now)\b',
            # Emotional transitions
            r'\b(suddenly|surprisingly|unfortunately|fortunately|interestingly|actually|honestly|frankly|basically)\b',
            # Question starters
            r'^\s*(what|how|why|when|where|who|which|do|does|did|can|could|would|should|will)\b',
            # Contrasting thoughts
            r'\b(but|although|though|while|whereas|on the other hand|in contrast|instead|rather)\b',
            # Speech patterns common in journal entries
            r'^\s*(so|and|well|ok|okay|right|actually|basically|you know)\b'
        ],
        'hi': [
            # Hindi transition words (Devanagari and transliterated)
            r'\b(लेकिन|हालांकि|फिर|अब|तो|और|किंतु|परंतु|इसलिए|क्योंकि|वैसे|anyway|however|lekin|phir|ab|toh|aur|isliye|kyunki|waise)\b',
            # Time transitions in Hindi
            r'\b(आज|कल|परसों|सुबह|शाम|रात|पहले|बाद में|अभी|today|kal|parso|subah|sham|raat|pehle|baad mein|abhi)\b',
            # Emotional transitions
            r'\b(अचानक|दुर्भाग्य से|खुशी की बात|वास्तव में|सच में|achanak|durbhagya se|khushi ki baat|waastav mein|sach mein)\b',
            # Speech patterns
            r'^\s*(तो|और|वैसे|देखिए|सुनिए|toh|aur|waise|dekhiye|suniye|so|and|well)\b'
        ],
        'es': [
            # Spanish transition words
            r'\b(sin embargo|mientras tanto|además|también|después|luego|finalmente|en conclusión|pero|aunque|entonces|ahora|hoy|ayer|mañana)\b',
            r'^\s*(entonces|y|bueno|así que|pues|vale)\b'
        ],
        'fr': [
            # French transition words
            r'\b(cependant|pendant ce temps|en outre|aussi|après|ensuite|finalement|en conclusion|mais|bien que|alors|maintenant|aujourd\'hui|hier|demain)\b',
            r'^\s*(alors|et|bon|donc|eh bien)\b'
        ],
        'de': [
            # German transition words
            r'\b(jedoch|währenddessen|außerdem|auch|danach|dann|schließlich|zusammenfassend|aber|obwohl|also|jetzt|heute|gestern|morgen)\b',
            r'^\s*(also|und|nun|so|ja)\b'
        ],
        'ja': [
            # Japanese transition words
            r'(しかし|そして|それから|でも|ところで|実は|今日|昨日|明日|今|さっき|後で|demo|shikashi|soshite|sorekara|tokorode|jitsuwa|kyou|kinou|ashita|ima|sakki|atode)\b',
            r'^\s*(そう|まあ|えーと|あの|sou|maa|eeto|ano|so|well)\b'
        ],
        'ar': [
            # Arabic transition words
            r'\b(لكن|ومع ذلك|أيضا|ثم|بعد ذلك|أخيرا|اليوم|أمس|غدا|الآن|lakin|wa ma3a zalik|aydan|thumma|ba3d zalik|akhiran|al-yawm|ams|ghadan|al-aan)\b',
            r'^\s*(إذن|و|حسنا|izn|wa|hasanan)\b'
        ]
    }
    
    # Default to English if language not supported
    return patterns.get(language, patterns['en'])

def format_journal_entry(raw_transcript: str, language: str = 'en') -> str:
    """
    Format a raw journal transcript for display with improved readability.
    
    Args:
        raw_transcript: Raw text from speech-to-text transcription
        
    Returns:
        Formatted text with paragraph breaks and improved structure
    """
    if not raw_transcript:
        return raw_transcript
    
    # Add paragraph breaks
    formatted_text = add_paragraph_breaks(raw_transcript, language)
    
    # Clean up any excessive whitespace
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    formatted_text = re.sub(r' {2,}', ' ', formatted_text)
    
    return formatted_text