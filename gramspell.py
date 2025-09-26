#!/usr/bin/env python3
"""
Refactored GramSpell for Web + CLI
- Spell-check with pyspellchecker
- Grammar/style check with language_tool_python
- Preserves punctuation and line breaks
- Returns structured results for web integration
"""

from spellchecker import SpellChecker
import language_tool_python
import nltk
import re
from typing import List, Dict, Tuple

# Ensure NLTK punkt data
nltk.download('punkt', quiet=True)

SPELLER = SpellChecker(language='en')
TOOL = language_tool_python.LanguageTool('en-US')


def tokenize_sentences(text: str) -> List[str]:
    return nltk.tokenize.sent_tokenize(text)


def word_tokenize(sentence: str) -> List[str]:
    """Preserve words including apostrophes for contractions."""
    return re.findall(r"[A-Za-z']+", sentence)


def suggest_spelling(word: str) -> List[str]:
    suggestions = list(SPELLER.candidates(word))
    best = SPELLER.correction(word)
    if best and best in suggestions:
        suggestions.remove(best)
        suggestions.insert(0, best)
    return suggestions


def spell_check_sentence(sentence: str, auto_apply: bool = False) -> Tuple[str, List[Dict]]:
    """Spell check a sentence and optionally auto-apply corrections."""
    issues = []
    corrected_sentence = sentence
    tokens = word_tokenize(sentence)

    for match in re.finditer(r"[A-Za-z']+", sentence):
        w = match.group()
        start, end = match.start(), match.end()
        lw = w.lower()

        if lw in SPELLER:
            continue

        suggestions = suggest_spelling(lw)
        applied = False
        if auto_apply and suggestions:
            repl = suggestions[0]
            if w[0].isupper():
                repl = repl.capitalize()
            corrected_sentence = corrected_sentence[:start] + repl + corrected_sentence[end:]
            applied = True
        issues.append({
            'word': w,
            'start': start,
            'end': end,
            'suggestions': suggestions,
            'applied': applied
        })

    return corrected_sentence, issues


def grammar_check_text(text: str, auto_apply: bool = False) -> Tuple[str, List[Dict]]:
    matches = TOOL.check(text)
    issues = []
    corrected_text = text
    shift = 0

    for m in matches:
        start = m.offset + shift
        end = start + m.errorLength
        replacements = m.replacements
        applied = False
        chosen = None
        if auto_apply and replacements:
            chosen = replacements[0]
            corrected_text = corrected_text[:start] + chosen + corrected_text[end:]
            shift += len(chosen) - m.errorLength
            applied = True
        issues.append({
            'message': m.message,
            'offset': start,
            'length': len(chosen) if chosen else m.errorLength,
            'context': m.context,
            'replacements': replacements,
            'ruleId': m.ruleId,
            'applied': applied
        })
    return corrected_text, issues


def correct_text_pipeline(text: str, auto_spell: bool = False, auto_grammar: bool = False) -> Dict:
    """Full pipeline: spell-check → grammar-check, preserving formatting."""
    lines = text.splitlines()
    spelled_lines = []
    spell_issues_all = []

    for line in lines:
        sentences = tokenize_sentences(line)
        corrected_sentences = []
        for sent in sentences:
            corrected_sent, issues = spell_check_sentence(sent, auto_apply=auto_spell)
            corrected_sentences.append(corrected_sent)
            for iss in issues:
                iss['sentence'] = sent
            spell_issues_all.extend(issues)
        spelled_lines.append(" ".join(corrected_sentences))

    intermediate_text = "\n".join(spelled_lines)
    final_text, grammar_issues = grammar_check_text(intermediate_text, auto_apply=auto_grammar)

    return {
        'original_text': text,
        'after_spell_text': intermediate_text,
        'final_text': final_text,
        'spell_issues': spell_issues_all,
        'grammar_issues': grammar_issues
    }


# ================================
# Example for Flask Integration
# ================================
def correct_text_for_web(text: str, auto_spell=True, auto_grammar=True) -> Dict:
    """
    Use this function in your Flask route.
    Returns a dictionary suitable for template rendering:
    {
        original_text, final_text, spell_issues, grammar_issues
    }
    """
    result = correct_text_pipeline(text, auto_spell=auto_spell, auto_grammar=auto_grammar)
    # Keep only what you want to show on web
    return {
        'original': result['original_text'],
        'corrected': result['final_text'],
        'spell_issues': result['spell_issues'],
        'grammar_issues': result['grammar_issues']
    }
