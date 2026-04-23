import streamlit as st
from datetime import date

from models import User, Plan, ACTIVITY_OPTIONS, TIME_WINDOWS, VIBES
from matching import match_plans, MatchResult
from sample_data import get_sample_plans

# ── Suggested plan generator ──────────────────────────────────────────────────

# Loose ordering: warm-up / social anchor → active middle → mellow close
_WARMUP   = {"coffee", "brunch", "yoga", "walk", "farmer's market", "bookstore"}
_ACTIVE   = {"hiking", "cycling", "climbing", "beach", "food tour", "picnic", "museums"}
_EVENING  = {"wine bar", "live music", "jazz club", "rooftop bar"}

def suggested_plan(target: Plan, match: "MatchResult") -> str:
    """
    Build a short narrative suggestion from the union of two plans' activities.
    Buckets activities into warm-up → active → wind-down and joins with →.
    Falls back gracefully when buckets are empty.
    """
    combined = list(dict.fromkeys(                       # dedupe, preserve order
        target.activities + match.plan.activities
    ))

    warmup  = [a for a in combined if a in _WARMUP]
    active  = [a for a in combined if a in _ACTIVE]
    evening = [a for a in combined if a in _EVENING]
    other   = [a for a in combined if a not in _WARMUP | _ACTIVE | _EVENING]

    # Build an ordered sequence: pick 1 from each non-empty bucket
    sequence = []
    if warmup:  sequence.append(warmup[0])
    if active:  sequence.append(active[0])
    if evening: sequence.append(evening[0])
    elif other: sequence.append(other[0])           # use leftover if no evening activity

    # Need at least 2 steps to be interesting; pad with remaining activities
    if len(sequence) < 2:
        extras = [a for a in combined if a not in sequence]
        sequence += extras[:2 - len(sequence)]

    if not sequence:
        return "Hang out and see where the day takes you."

    return " → ".join(sequence)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Bay Area Plans",
    page_icon="🌁",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
    font-weight: 400 !important;
}

/* Section cards */
.section-card {
    background: #f7f5f2;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border: 1px solid #e8e4de;
}

/* Match cards */
.match-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 14px;
    border: 1px solid #e8e4de;
    position: relative;
}

.match-rank {
    font-family: 'DM Serif Display', serif;
    font-size: 13px;
    color: #9e8f7e;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}

.match-name {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    color: #1a1a18;
    margin-bottom: 4px;
}

.match-score-bar-bg {
    background: #ede9e3;
    border-radius: 99px;
    height: 6px;
    width: 100%;
    margin: 10px 0 14px;
}

.match-score-bar-fill {
    background: #2e7d52;
    border-radius: 99px;
    height: 6px;
}

.match-meta {
    font-size: 13px;
    color: #6b6358;
    line-height: 1.7;
}

.match-meta strong {
    color: #1a1a18;
    font-weight: 500;
}

.tag {
    display: inline-block;
    background: #eef6f1;
    color: #2e7d52;
    border-radius: 99px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 500;
    margin: 2px 2px 2px 0;
}

.vibe-tag {
    display: inline-block;
    background: #f0ebe3;
    color: #7a5c3a;
    border-radius: 99px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 500;
}

.explanation {
    font-size: 13px;
    color: #6b6358;
    background: #f7f5f2;
    border-radius: 8px;
    padding: 10px 14px;
    margin-top: 10px;
    border-left: 3px solid #c5b9a8;
    line-height: 1.6;
}

.suggested-plan {
    font-size: 13px;
    color: #2e5c3e;
    background: #eef6f1;
    border-radius: 8px;
    padding: 10px 14px;
    margin-top: 8px;
    border-left: 3px solid #2e7d52;
    line-height: 1.6;
}

.score-pct {
    font-family: 'DM Serif Display', serif;
    font-size: 20px;
    color: #2e7d52;
    font-weight: 400;
}

.no-matches {
    text-align: center;
    padding: 40px 24px;
    color: #9e8f7e;
    font-size: 15px;
}

.plan-count {
    font-size: 13px;
    color: #9e8f7e;
    margin-bottom: 20px;
}

/* Streamlit overrides */
div[data-testid="stButton"] button {
    background-color: #1a1a18 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 28px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    width: 100% !important;
    transition: background 0.2s !important;
}
div[data-testid="stButton"] button:hover {
    background-color: #2e7d52 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

if "plans" not in st.session_state:
    st.session_state.plans = get_sample_plans()

if "latest_plan" not in st.session_state:
    st.session_state.latest_plan = None

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("# 🌁 Bay Area Plans")
st.markdown("Find people doing the same things, on the same day.")
st.divider()

# ── Section 1: Create a Plan ──────────────────────────────────────────────────

st.markdown("## Create a plan")
st.markdown(
    f"<div class='plan-count'>{len(st.session_state.plans)} plans in the pool</div>",
    unsafe_allow_html=True,
)

with st.form("create_plan_form"):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Your name", placeholder="e.g. Maya")
        city = st.text_input("City", value="Bay Area")
        plan_date = st.date_input("Date", value=date(2024, 8, 15))

    with col2:
        time_window = st.selectbox("Time window", TIME_WINDOWS)
        vibe            = st.selectbox("Vibe", VIBES)
        max_group_size  = st.slider("Max group size", min_value=2, max_value=6, value=4)

    activities = st.multiselect(
        "Activities  (pick at least one)",
        options=ACTIVITY_OPTIONS,
        default=["coffee"],
    )

    submitted = st.form_submit_button("Find my matches →")

if submitted:
    if not name.strip():
        st.warning("Please enter your name.")
    elif not activities:
        st.warning("Pick at least one activity.")
    else:
        user = User(name=name.strip())
        new_plan = Plan(
            user_id     = user.id,
            user_name   = user.name,
            city        = city,
            date        = plan_date,
            time_window = time_window,
            activities  = activities,
            vibe           = vibe,
            max_group_size = max_group_size,
        )
        st.session_state.plans.append(new_plan)
        st.session_state.latest_plan = new_plan
        st.success(f"Plan created for **{user.name.title()}**! Scroll down to see your matches.")

st.divider()

# ── Section 2: Matches ────────────────────────────────────────────────────────

st.markdown("## Top matches")

target = st.session_state.latest_plan

if target is None:
    st.markdown("""
        <div class='no-matches'>
            <div style='font-size:32px;margin-bottom:12px'>🗓️</div>
            <strong>No plan yet.</strong><br>
            Fill in the form above and hit <em>Find my matches</em> to get started.
        </div>
    """, unsafe_allow_html=True)
else:
    # Show the submitted plan as a compact summary
    with st.expander("Your plan", expanded=False):
        tags = " ".join(f"<span class='tag'>{a}</span>" for a in target.activities)
        st.markdown(f"""
        <div class='match-meta'>
            <strong>Name</strong> &nbsp; {target.user_name.title()}<br>
            <strong>City</strong> &nbsp; {target.city.title()}<br>
            <strong>Date</strong> &nbsp; {target.date}<br>
            <strong>Window</strong> &nbsp; {target.time_window} &nbsp;·&nbsp;
            <strong>Vibe</strong> &nbsp; <span class='vibe-tag'>{target.vibe}</span><br>
            <strong>Activities</strong> &nbsp; {tags}<br>
            <strong>Group size</strong> &nbsp; up to {target.max_group_size}
        </div>
        """, unsafe_allow_html=True)

    # Explicit same-user guard (belt-and-suspenders on top of match_plans filter)
    other_plans = [p for p in st.session_state.plans if p.user_id != target.user_id]
    matches = match_plans(target, other_plans)

    if not matches:
        st.markdown("""
            <div class='no-matches'>
                <div style='font-size:32px;margin-bottom:12px'>🔍</div>
                <strong>No matches found.</strong><br>
                Nobody else has a plan for that city and date yet.<br>
                <span style='font-size:12px;color:#b8ac9e'>Try a different date, or share this app so others can add plans.</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        rank_labels = ["Best match", "2nd match", "3rd match"]

        for i, m in enumerate(matches):
            score_pct = round(m.score * 100)
            act_tags  = " ".join(f"<span class='tag'>{a}</span>" for a in m.plan.activities)
            suggestion = suggested_plan(target, m)

            st.markdown(f"""
            <div class='match-card'>
                <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                    <div>
                        <div class='match-rank'>{rank_labels[i]}</div>
                        <div class='match-name'>{m.plan.user_name.title()}</div>
                    </div>
                    <div class='score-pct'>{score_pct}%</div>
                </div>

                <div class='match-score-bar-bg'>
                    <div class='match-score-bar-fill' style='width:{score_pct}%'></div>
                </div>

                <div class='match-meta'>
                    <strong>Window</strong> &nbsp; {m.plan.time_window} &nbsp;·&nbsp;
                    <strong>Vibe</strong> &nbsp; <span class='vibe-tag'>{m.plan.vibe}</span> &nbsp;·&nbsp;
                    <strong>Group</strong> &nbsp; up to {min(target.max_group_size, m.plan.max_group_size)}
                </div>

                <div style='margin-top:10px'>{act_tags}</div>

                <div class='suggested-plan'>✦ &nbsp;{suggestion}</div>
                <div class='explanation'>💬 &nbsp;{m.explanation}</div>
            </div>
            """, unsafe_allow_html=True)
