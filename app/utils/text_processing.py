"""
Text processing utilities for improving readability of transcribed journal entries.

This module provides functions for formatting continuous speech-to-text output
into well-structured, readable paragraphs.
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def add_paragraph_breaks(text: str) -> str:
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
    
    # Split into sentences using common sentence endings
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
    
    # Patterns that suggest new paragraph should start
    new_paragraph_indicators = [
        # Topic transition words
        r'\b(anyway|however|meanwhile|additionally|furthermore|moreover|besides|also|next|then|afterwards|later|finally|lastly|in conclusion|to summarize)\b',
        # Time transitions
        r'\b(today|yesterday|tomorrow|this morning|this afternoon|this evening|last week|next week|recently|earlier|afterwards)\b',
        # Emotional transitions
        r'\b(suddenly|surprisingly|unfortunately|fortunately|interestingly|actually|honestly|frankly|basically)\b',
        # Question starters
        r'^\s*(what|how|why|when|where|who|which|do|does|did|can|could|would|should|will)\b',
        # Contrasting thoughts
        r'\b(but|although|though|while|whereas|on the other hand|in contrast|instead|rather)\b'
    ]
    
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in new_paragraph_indicators]
    
    for i, sentence in enumerate(reconstructed_sentences):
        current_paragraph.append(sentence)
        
        # Determine if we should start a new paragraph
        should_break = False
        
        # Check if current paragraph is getting long (more than 3 sentences)
        if len(current_paragraph) >= 3:
            should_break = True
        
        # Check if next sentence (if exists) starts with transition words
        elif i + 1 < len(reconstructed_sentences):
            next_sentence = reconstructed_sentences[i + 1]
            for pattern in compiled_patterns:
                if pattern.search(next_sentence):
                    should_break = True
                    break
        
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
    
    return formatted_text


def format_journal_entry(raw_transcript: str) -> str:
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
    formatted_text = add_paragraph_breaks(raw_transcript)
    
    # Clean up any excessive whitespace
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    formatted_text = re.sub(r' {2,}', ' ', formatted_text)
    
    return formatted_text