import streamlit as st
import json
import random
import re
import io
from gtts import gTTS

# ── Data ─────────────────────────────────────────────────────────────────────

PROGRESS_FILE = "data/progress.json"

with open("data/tone_map.json", "r", encoding="utf-8") as _f:
    _TONE_MAP = json.load(_f)

with open("data/flashcards.json", "r", encoding="utf-8") as _f:
    all_cards = json.load(_f)

MAX_CATEGORY = max(c["category"] for c in all_cards)


# ── Pinyin conversion ─────────────────────────────────────────────────────────

def numeral_to_diacritic(text: str) -> str:
    def replace_syllable(m):
        vowels, tone = m.group(1).lower(), int(m.group(2))
        chars = list(vowels)
        target = None
        for idx, ch in enumerate(chars):
            if ch in ("a", "e"):
                target = idx
                break
        if target is None:
            ou = vowels.find("ou")
            if ou != -1:
                target = ou
        if target is None:
            for idx in range(len(chars) - 1, -1, -1):
                if chars[idx] in _TONE_MAP:
                    target = idx
                    break
        if target is not None and chars[target] in _TONE_MAP:
            chars[target] = _TONE_MAP[chars[target]][tone - 1]
        return "".join(chars)

    normalised = re.sub(r"\(([1-5])\)", r"\1", text.lower())
    result = re.sub(r"([a-züv]+)([1-5])", replace_syllable, normalised)
    return result.replace(" ", "")


# ── UI helpers ────────────────────────────────────────────────────────────────

@st.cache_data
def _tts_audio(text: str) -> bytes:
    buf = io.BytesIO()
    gTTS(text=text, lang="zh-CN").write_to_fp(buf)
    return buf.getvalue()

def speak_button(text: str):
    st.audio(_tts_audio(text), format="audio/mp3")


# ── Persistence ───────────────────────────────────────────────────────────────

def load_progress() -> dict:
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"categories": {}}

def save_progress():
    progress = load_progress()
    cat_key = str(st.session_state.category)
    progress["categories"][cat_key] = {
        "mastered": list(st.session_state.mastered),
        "streaks": st.session_state.streaks,
        "correct": st.session_state.correct,
        "incorrect": st.session_state.incorrect,
    }
    progress["card_stats"] = st.session_state.card_stats
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ── Card / session helpers ────────────────────────────────────────────────────

def get_category_cards(category: int) -> list:
    return [c for c in all_cards if c["category"] == category]

def _weighted_pick(candidates: list, exclude_hanzi: str | None = None) -> dict | None:
    """Pick a card using weighted random selection, prioritising cards with more
    incorrect answers. Excludes the current card when possible to avoid repeats."""
    card_stats = st.session_state.get("card_stats", {})
    pool = [c for c in candidates if c["hanzi"] != exclude_hanzi] or candidates
    if not pool:
        return None
    weights = [card_stats.get(c["hanzi"], {}).get("incorrect", 0) + 1 for c in pool]
    return random.choices(pool, weights=weights, k=1)[0]

def next_card() -> dict | None:
    """Return the next unmastered card, prioritised by incorrect count. None if all mastered."""
    mastered = st.session_state.mastered
    current  = st.session_state.card
    remaining = [c for c in get_category_cards(st.session_state.category) if c["hanzi"] not in mastered]
    if not remaining:
        return None
    return _weighted_pick(remaining, exclude_hanzi=current["hanzi"] if current else None)

def init_category(category: int):
    cat_cards = get_category_cards(category)
    progress  = load_progress()
    saved     = progress.get("categories", {}).get(str(category), {})

    mastered  = set(saved.get("mastered", []))
    streaks   = saved.get("streaks", {})
    correct   = saved.get("correct", 0)
    incorrect = saved.get("incorrect", 0)

    remaining = [c for c in cat_cards if c["hanzi"] not in mastered]

    # Seed card_stats from disk so _weighted_pick can use it at init time
    if "card_stats" not in st.session_state:
        st.session_state.card_stats = progress.get("card_stats", {})

    st.session_state.category      = category
    st.session_state.category_size = len(cat_cards)
    st.session_state.mastered      = mastered
    st.session_state.streaks       = streaks
    st.session_state.correct       = correct
    st.session_state.incorrect     = incorrect
    st.session_state.card          = _weighted_pick(remaining) if remaining else None
    st.session_state.checked       = False
    st.session_state.last_correct  = None
    st.session_state.round_count   = 0
    st.session_state.graduated     = len(mastered) == len(cat_cards)
    st.session_state.ended         = False
    st.session_state.selecting     = False


def render_category_selection():
    st.markdown("### Choose a category")
    saved_cats = load_progress().get("categories", {})

    options = []
    for cat in range(1, MAX_CATEGORY + 1):
        n_mastered = len(saved_cats.get(str(cat), {}).get("mastered", []))
        label = f"Category {cat}  (ranks {(cat-1)*100+1}–{cat*100})  —  {n_mastered}/100 mastered"
        options.append(label)

    choice_label = st.selectbox("Category", options, index=0)
    chosen_cat = options.index(choice_label) + 1

    if st.button("Start"):
        init_category(chosen_cat)
        st.rerun()


def render_graduation():
    cat       = st.session_state.category
    correct   = st.session_state.correct
    incorrect = st.session_state.incorrect
    answered  = correct + incorrect
    st.balloons()
    st.markdown(f"## Category {cat} complete!")
    st.markdown("You answered every character correctly 5 times in a row.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Answered", answered)
    col2.metric("Correct", correct)
    col3.metric("Incorrect", incorrect)
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if cat < MAX_CATEGORY:
            if st.button(f"Advance to Category {cat + 1}"):
                init_category(cat + 1)
                st.rerun()
        else:
            st.markdown("### You've mastered all 2500 characters!")
    with col_b:
        if st.button("Choose category"):
            st.session_state.selecting = True
            st.rerun()
