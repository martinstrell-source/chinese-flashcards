import logging
import unicodedata
import streamlit as st
from datetime import datetime
from hanzipy.decomposer import HanziDecomposer
from utils.utils import numeral_to_diacritic, save_progress, all_cards

logging.getLogger().setLevel(logging.WARNING)
_decomposer = HanziDecomposer()
logging.getLogger().setLevel(logging.NOTSET)

def _all_components(hanzi: str, seen: set | None = None) -> set:
    if seen is None:
        seen = set()
    if hanzi in seen:
        return set()
    seen.add(hanzi)
    parts = set(_decomposer.decompose(hanzi, 1).get("components", []))
    parts.discard("No glyph available")
    parts.discard(hanzi)
    result = set()
    for p in parts:
        result.add(p)
        result |= _all_components(p, seen)
    return result

def _visual_similarity(a: str, b: str) -> float:
    ca, cb = _all_components(a), _all_components(b)
    if not ca or not cb:
        return 0.0
    return len(ca & cb) / len(ca | cb)

def _find_confused_card(current_hanzi: str, guess_pinyin: str) -> dict | None:
    best, best_score = None, 0.0
    for card in all_cards:
        if card["hanzi"] == current_hanzi:
            continue
        if _strip_tones(guess_pinyin) != _strip_tones(card["pinyin"]):
            continue
        score = _visual_similarity(current_hanzi, card["hanzi"])
        if score > best_score:
            best_score, best = score, card
    return best if best_score >= 0.5 else None

def _strip_tones(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def check_mastery(hanzi: str, new_streak: int, category_size: int):
    if new_streak >= 5:
        st.session_state.mastered.add(hanzi)
        if len(st.session_state.mastered) == category_size:
            st.session_state.graduated = True

def update_card_stats(hanzi: str, is_correct: bool):
    stats = st.session_state.card_stats.get(hanzi, {
        "times_used": 0, "correct": 0, "incorrect": 0, "last_tested": None,
        "memory_strength": 0.5,
    })
    stats["times_used"] += 1
    stats["correct" if is_correct else "incorrect"] += 1
    stats["last_tested"] = datetime.now().isoformat()
    st.session_state.card_stats[hanzi] = stats

def update_memory_strength(hanzi: str, is_correct: bool):
    stats = st.session_state.card_stats[hanzi]
    delta = 0.1 if is_correct else -0.2
    stats["memory_strength"] = max(0.0, min(1.0, stats.get("memory_strength", 0.5) + delta))

def check_answer(guess: str, card: dict, category_size: int):
    hanzi      = card["hanzi"]
    normalised = numeral_to_diacritic(guess.strip())
    is_correct = normalised == card["pinyin"]
    wrong_tone = not is_correct and _strip_tones(normalised) == _strip_tones(card["pinyin"])
    st.session_state.wrong_tone    = wrong_tone
    st.session_state.confused_card = _find_confused_card(hanzi, normalised) if not is_correct and not wrong_tone else None

    st.session_state.last_correct = is_correct
    st.session_state.checked      = True

    update_card_stats(hanzi, is_correct)
    update_memory_strength(hanzi, is_correct)

    if is_correct:
        st.session_state.correct += 1
        new_streak = st.session_state.streaks.get(hanzi, 0) + 1
        st.session_state.streaks[hanzi] = new_streak
        check_mastery(hanzi, new_streak, category_size)
    else:
        st.session_state.incorrect += 1
        st.session_state.streaks[hanzi] = 0

    save_progress()
