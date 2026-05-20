import streamlit as st
import streamlit.components.v1 as components
from utils.utils import (
    all_cards, MAX_CATEGORY,
    speak_button,
    load_progress,
    next_card, init_category, render_graduation, render_category_selection,
)
from utils.scoring import check_answer

st.set_page_config(page_title="Chinese Flashcards", layout="centered")

# ── Bootstrap ─────────────────────────────────────────────────────────────────

if "selecting" not in st.session_state:
    st.session_state.selecting = True
if "card_stats" not in st.session_state:
    st.session_state.card_stats = load_progress().get("card_stats", {})

st.title("Chinese Flashcards")
st.markdown("<style>[data-testid='stFormSubmitButton']{display:none}</style>", unsafe_allow_html=True)

# ── Category selection screen ─────────────────────────────────────────────────

if st.session_state.selecting:
    render_category_selection()

# ── Graduation screen ─────────────────────────────────────────────────────────

elif st.session_state.graduated:
    render_graduation()

# ── Paused / end-run screen ───────────────────────────────────────────────────

elif st.session_state.ended:
    cat = st.session_state.category
    mastered_count = len(st.session_state.mastered)
    category_size  = st.session_state.category_size
    correct        = st.session_state.correct
    incorrect      = st.session_state.incorrect
    answered       = correct + incorrect
    st.markdown("### Session paused")
    col1, col2, col3 = st.columns(3)
    col1.metric("Category", cat)
    col2.metric("Mastered", f"{mastered_count} / {category_size}")
    col3.metric("Remaining", category_size - mastered_count)
    st.divider()
    st.markdown("**This session**")
    col4, col5, col6 = st.columns(3)
    col4.metric("Answered", answered)
    col5.metric("Correct", correct)
    col6.metric("Incorrect", incorrect)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Continue"):
            st.session_state.ended = False
            st.rerun()
    with col_b:
        if st.button("Choose category"):
            st.session_state.selecting = True
            st.rerun()

# ── Main card view ────────────────────────────────────────────────────────────

else:
    card           = st.session_state.card
    mastered_count = len(st.session_state.mastered)
    category_size  = st.session_state.category_size
    cat            = st.session_state.category

    st.markdown(f"**Category {cat}** — {mastered_count} / {category_size} mastered")
    st.progress(mastered_count / category_size)
    st.caption(f"✓ {st.session_state.correct}   ✗ {st.session_state.incorrect}")

    st.markdown(f"# {card['hanzi']}")

    stats = st.session_state.card_stats.get(card["hanzi"], {})
    if stats:
        last = stats["last_tested"][:10] if stats.get("last_tested") else "—"
        st.caption(
            f"Tested {stats['times_used']}×  |  "
            f"✓ {stats['correct']}  ✗ {stats['incorrect']}  |  "
            f"Last: {last}"
        )
    else:
        st.caption("Never tested")

    streak = st.session_state.streaks.get(card["hanzi"], 0)
    st.caption("⭐" * streak + "☆" * (5 - streak) + f"  {streak}/5")

    with st.form(f"pinyin_form_{st.session_state.round_count}"):
        guess = st.text_input("Enter pinyin:", disabled=st.session_state.checked)
        submitted = st.form_submit_button("check")

    if not st.session_state.checked:
        components.html(
            "<script>window.parent.document.querySelector('[data-testid=\"stTextInput\"] input').focus();</script>",
            height=0,
        )

    if submitted and not st.session_state.checked:
        check_answer(guess, card, category_size)
        st.rerun()

    if st.button("New Card", disabled=not st.session_state.checked):
        if not st.session_state.graduated:
            nxt = next_card()
            if nxt is None:
                st.session_state.graduated = True
            else:
                st.session_state.card         = nxt
                st.session_state.checked      = False
                st.session_state.last_correct = None
                st.session_state.round_count += 1
        st.rerun()

    if st.session_state.checked:
        hanzi = card["hanzi"]
        if st.session_state.last_correct:
            if hanzi in st.session_state.mastered:
                st.success("Correct! Character mastered!")
            else:
                st.success(f"Correct! Streak: {st.session_state.streaks.get(hanzi, 0)}/5")
        else:
            st.error("Incorrect — streak reset to 0")
        st.markdown(f"**{card['pinyin']}** — {card['meaning']}")
        speak_button(card["hanzi"])

    st.divider()
    if st.button("End run"):
        st.session_state.ended = True
        st.rerun()
