import streamlit as st
from datetime import datetime
from utils.utils import numeral_to_diacritic, save_progress

def check_mastery(hanzi: str, new_streak: int, category_size: int):
    if new_streak >= 5:
        st.session_state.mastered.add(hanzi)
        if len(st.session_state.mastered) == category_size:
            st.session_state.graduated = True

def update_card_stats(hanzi: str, is_correct: bool):
    stats = st.session_state.card_stats.get(hanzi, {
        "times_used": 0, "correct": 0, "incorrect": 0, "last_tested": None,
    })
    stats["times_used"] += 1
    stats["correct" if is_correct else "incorrect"] += 1
    stats["last_tested"] = datetime.now().isoformat()
    st.session_state.card_stats[hanzi] = stats

def check_answer(guess: str, card: dict, category_size: int):
    hanzi      = card["hanzi"]
    is_correct = numeral_to_diacritic(guess.strip()) == card["pinyin"]

    st.session_state.last_correct = is_correct
    st.session_state.checked      = True

    update_card_stats(hanzi, is_correct)

    if is_correct:
        st.session_state.correct += 1
        new_streak = st.session_state.streaks.get(hanzi, 0) + 1
        st.session_state.streaks[hanzi] = new_streak
        check_mastery(hanzi, new_streak, category_size)
    else:
        st.session_state.incorrect += 1
        st.session_state.streaks[hanzi] = 0

    save_progress()
