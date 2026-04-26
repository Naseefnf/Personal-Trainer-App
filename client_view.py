"""
client_view.py
────────────────────────────────────────────────
Client Dashboard:
  - View trainer's daily plan
  - Toggle diet meals and exercises as completed
  - Write remarks/notes
  - Submit progress to Firestore
"""

import streamlit as st
from datetime import datetime
from firebase_service import get_today_plan, submit_client_status, get_client_status


def show_client_dashboard():
    user = st.session_state.user

    # ── Header ────────────────────────────────────────────────────────────────
    col_title, col_logout = st.columns([9, 1])
    with col_title:
        st.markdown("## 🏃 My Daily Plan")
        st.markdown(
            f"Hello, **{user['displayName']}** &nbsp;|&nbsp; "
            f"📅 {datetime.now().strftime('%A, %d %B %Y')}"
        )
    with col_logout:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.markdown("---")

    # ── Guard: trainer must be linked ────────────────────────────────────────
    trainer_uid = user.get("trainerUid")
    if not trainer_uid:
        st.error(
            "⚠️ Your account is not linked to any trainer. "
            "Please contact your trainer and re-register with their UID."
        )
        return

    # ── Load plan ─────────────────────────────────────────────────────────────
    with st.spinner("Loading today's plan…"):
        plan = get_today_plan(trainer_uid)

    if not plan:
        st.info(
            "⏳ Your trainer hasn't published today's plan yet. "
            "Check back soon or contact your trainer."
        )
        return

    # ── Load existing submission (for pre-filling) ────────────────────────────
    existing = get_client_status(user["uid"])
    already_submitted = existing is not None
    prev_completed = set(existing.get("completedTasks", []) if existing else [])
    prev_remarks   = existing.get("remarks", "") if existing else ""

    if already_submitted:
        st.success("✅ You've already submitted today's progress. You can update it anytime.")

    # ── Diet Plan ─────────────────────────────────────────────────────────────
    st.subheader("🥗 Diet Plan")
    diet_meals     = plan.get("dietPlan", [])
    total_cal_plan = sum(m.get("calories", 0) for m in diet_meals)
    st.caption(f"Total daily calories: **{total_cal_plan} kcal**")

    diet_completed = []
    for meal in diet_meals:
        meal_name   = meal.get("meal", "Meal")
        items       = meal.get("items", [])
        calories    = meal.get("calories", 0)
        items_str   = " · ".join(items) if items else "—"

        checked = st.checkbox(
            f"**{meal_name}** &nbsp; {items_str} &nbsp; *(_{calories} kcal_)*",
            value=(meal_name in prev_completed),
            key=f"diet_cb_{meal_name}",
        )
        if checked:
            diet_completed.append(meal_name)

    completed_cal = sum(
        m.get("calories", 0)
        for m in diet_meals
        if m.get("meal") in diet_completed
    )
    st.caption(f"Consumed so far: **{completed_cal} / {total_cal_plan} kcal**")

    st.markdown("---")

    # ── Exercise Routine ──────────────────────────────────────────────────────
    st.subheader("🏋️ Exercise Routine")
    exercises = plan.get("exerciseRoutine", [])

    exercise_completed = []
    for ex in exercises:
        ex_name     = ex.get("name", "Exercise")
        sets        = ex.get("sets", 0)
        reps        = ex.get("reps", 0)
        youtube_url = ex.get("youtube_url", "").strip()
        label       = f"**{ex_name}** &nbsp; {sets} sets × {reps} reps/sec"

        col_check, col_link = st.columns([6, 1])
        with col_check:
            checked = st.checkbox(
                label,
                value=(ex_name in prev_completed),
                key=f"ex_cb_{ex_name}",
            )
        with col_link:
            if youtube_url:
                st.markdown(
                    f'<a href="{youtube_url}" target="_blank" '
                    f'style="text-decoration:none; font-size:22px;" '
                    f'title="Watch tutorial on YouTube">▶️</a>',
                    unsafe_allow_html=True,
                )
        if checked:
            exercise_completed.append(ex_name)

    st.markdown("---")

    # ── Overall progress bar ──────────────────────────────────────────────────
    all_tasks     = [m["meal"] for m in diet_meals] + [e["name"] for e in exercises]
    all_completed = diet_completed + exercise_completed
    total_tasks   = len(all_tasks)
    done_count    = len(all_completed)

    if total_tasks > 0:
        pct = done_count / total_tasks
        st.progress(
            pct,
            text=f"Overall progress: **{done_count}/{total_tasks}** tasks "
                 f"({int(pct * 100)}% complete)"
        )
    st.markdown("---")

    # ── Remarks ───────────────────────────────────────────────────────────────
    st.subheader("📝 Remarks / Notes to Trainer")
    remarks = st.text_area(
        "Share how you felt, any difficulties, or questions for your trainer:",
        value=prev_remarks,
        placeholder=(
            "e.g. Felt great today! Struggled a little with planks — "
            "could only hold 30 seconds. Can we add stretching tomorrow?"
        ),
        height=130,
    )

    # ── Submit ────────────────────────────────────────────────────────────────
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn_label = "🔄 Update My Submission" if already_submitted else "📤 Submit Progress to Trainer"
        if st.button(btn_label, use_container_width=True, type="primary"):
            today    = datetime.now().strftime("%Y-%m-%d")
            plan_id  = f"{trainer_uid}_{today}"
            with st.spinner("Submitting…"):
                submit_client_status(
                    client_uid      = user["uid"],
                    trainer_uid     = trainer_uid,
                    plan_id         = plan_id,
                    completed_tasks = all_completed,
                    remarks         = remarks.strip(),
                )
            st.success("✅ Progress submitted! Your trainer can now see your update.")
            st.rerun()
