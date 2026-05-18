import streamlit as st
import streamlit.components.v1 as components
import json
import random
import re

# Vowel → [tone1, tone2, tone3, tone4, tone5(neutral)]
_TONE_MAP = {
    "a": ["ā", "á", "ǎ", "à", "a"],
    "e": ["ē", "é", "ě", "è", "e"],
    "i": ["ī", "í", "ǐ", "ì", "i"],
    "o": ["ō", "ó", "ǒ", "ò", "o"],
    "u": ["ū", "ú", "ǔ", "ù", "u"],
    "ü": ["ǖ", "ǘ", "ǚ", "ǜ", "ü"],
    "v": ["ǖ", "ǘ", "ǚ", "ǜ", "ü"],  # v is a common alias for ü
}

def numeral_to_diacritic(text: str) -> str:
    """Convert numeral-tone pinyin (ni3 hao3) to diacritic pinyin (nǐhǎo)."""
    def replace_syllable(m):
        vowels, tone = m.group(1).lower(), int(m.group(2))
        chars = list(vowels)
        target = None
        for idx, ch in enumerate(chars):        # Rule 1: a or e takes the mark
            if ch in ("a", "e"):
                target = idx
                break
        if target is None:                      # Rule 2: in "ou", o takes it
            ou = vowels.find("ou")
            if ou != -1:
                target = ou
        if target is None:                      # Rule 3: last vowel takes it
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


def speak_button(text: str):
    safe = text.replace("'", "\\'")
    components.html(f"""
        <button onclick="(function(){{
            var u = new SpeechSynthesisUtterance('{safe}');
            u.lang = 'zh-CN';
            u.rate = 0.8;
            window.speechSynthesis.speak(u);
        }})()" style="
            background: transparent;
            border: 1px solid rgba(250,250,250,0.2);
            border-radius: 8px;
            color: rgb(250,250,250);
            cursor: pointer;
            font-size: 20px;
            padding: 6px 20px;
        ">🔊</button>
    """, height=48)

st.set_page_config(page_title="Chinese Flashcards", layout="centered")

with open("flashcards.json", "r") as f:
    cards = json.load(f)

total = st.session_state.get("total", len(cards))

def init_session(deck=None):
    if deck is None:
        deck = cards.copy()
    random.shuffle(deck)
    st.session_state.queue = deck[1:]
    st.session_state.card = deck[0]
    st.session_state.checked = False
    st.session_state.last_correct = None
    st.session_state.correct = 0
    st.session_state.incorrect = 0
    st.session_state.answered = 0
    st.session_state.total = len(deck)
    st.session_state.missed = []
    st.session_state.finished = False

if "card" not in st.session_state:
    init_session()

st.title("Chinese Flashcards")

if st.session_state.finished:
    correct = st.session_state.correct
    incorrect = st.session_state.incorrect
    answered = st.session_state.answered
    st.markdown("### Round complete!" if answered == total else "### Round ended early")
    col1, col2, col3 = st.columns(3)
    col1.metric("Answered", f"{answered} / {total}")
    col2.metric("Correct", correct)
    col3.metric("Incorrect", incorrect)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Start Over"):
            init_session()
            st.rerun()
    with col_b:
        missed = st.session_state.get("missed", [])
        if missed and st.button(f"Replay Incorrect ({len(missed)})"):
            init_session(deck=missed)
            st.rerun()
else:
    answered = st.session_state.answered
    st.progress(answered / total, text=f"{answered} / {total} cards")
    st.caption(f"✓ {st.session_state.correct}   ✗ {st.session_state.incorrect}")

    card = st.session_state.card
    st.markdown(f"# {card['hanzi']}")

    guess = st.text_input("Enter pinyin:", key=f"guess_{answered}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Check Answer", disabled=st.session_state.checked):
            is_correct = numeral_to_diacritic(guess.strip()) == card["pinyin"]
            st.session_state.last_correct = is_correct
            st.session_state.checked = True
            st.session_state.answered += 1
            if is_correct:
                st.session_state.correct += 1
            else:
                st.session_state.incorrect += 1
                st.session_state.missed.append(card)
            if st.session_state.answered == total:
                st.session_state.finished = True
            st.rerun()

    with col2:
        if st.button("New Card", disabled=not st.session_state.checked):
            st.session_state.card = st.session_state.queue.pop(0)
            st.session_state.checked = False
            st.session_state.last_correct = None
            st.rerun()

    if st.session_state.checked:
        if st.session_state.last_correct:
            st.success("Correct!")
        else:
            st.error("Incorrect")
        st.markdown(f"**{card['pinyin']}** — {card['meaning']}")

    st.divider()
    if st.button("End run"):
        st.session_state.finished = True
        st.rerun()
