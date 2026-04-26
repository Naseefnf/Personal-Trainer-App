"""
trainer_view.py
────────────────────────────────────────────────
Trainer Dashboard:
  Tab 1 — Upload today's Diet Plan + Exercise Routine
  Tab 2 — View all clients' completion status and remarks
"""

import streamlit as st
from datetime import datetime
from firebase_service import (
    upsert_daily_plan,
    get_all_client_statuses,
    get_trainer_clients,
)


def show_trainer_dashboard():
    user = st.session_state.user

    # ── Header ────────────────────────────────────────────────────────────────
    col_title, col_logout = st.columns([9, 1])
    with col_title:
        st.markdown(f"## 🏋️ Trainer Dashboard")
        st.markdown(
            f"Welcome back, **{user['displayName']}** &nbsp;|&nbsp; "
            f"📅 {datetime.now().strftime('%A, %d %B %Y')}"
        )
    with col_logout:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.info(
        f"🔑 **Your Trainer UID** (share this with your clients so they can link to you):\n\n"
        f"`{user['uid']}`"
    )
    st.markdown("---")

    tab_plan, tab_progress = st.tabs(["📋 Upload Today's Plan", "📊 Client Progress"])

    with tab_plan:
        _plan_upload_tab(user["uid"])

    with tab_progress:
        _client_progress_tab(user["uid"])


# ─── TAB 1: PLAN UPLOAD ───────────────────────────────────────────────────────

def _plan_upload_tab(trainer_uid: str):
    st.subheader("Build Today's Plan")
    st.caption("Clients will see this the moment you click Publish.")

    # ── Diet Plan ─────────────────────────────────────────────────────────────
    st.markdown("### 🥗 Diet Plan")

    # Default meals on first load
    if "diet_items" not in st.session_state:
        st.session_state.diet_items = [
            {"meal": "Breakfast", "items": "Oats, Eggs, Banana", "calories": 450},
            {"meal": "Lunch",     "items": "Rice, Grilled Chicken, Salad", "calories": 650},
            {"meal": "Dinner",    "items": "Chapati, Dal, Vegetables", "calories": 500},
        ]

    diet_plan = []
    for i, meal in enumerate(st.session_state.diet_items):
        with st.container(border=True):
            col_label, col_del = st.columns([10, 1])
            with col_label:
                st.markdown(f"**{meal['meal']}**")
            with col_del:
                if st.button("✕", key=f"del_diet_{i}", help="Remove this meal"):
                    st.session_state.diet_items.pop(i)
                    st.rerun()

            col_items, col_cal = st.columns([3, 1])
            with col_items:
                items_val = st.text_input(
                    "Food items (comma-separated)",
                    value=meal["items"],
                    key=f"diet_items_val_{i}",
                    placeholder="e.g. Oats, Eggs, Milk",
                )
            with col_cal:
                cal_val = st.number_input(
                    "Calories (kcal)",
                    value=meal["calories"],
                    min_value=0,
                    max_value=5000,
                    step=50,
                    key=f"diet_cal_val_{i}",
                )
        diet_plan.append({
            "meal":     meal["meal"],
            "items":    [x.strip() for x in items_val.split(",") if x.strip()],
            "calories": cal_val,
        })

    # Add custom meal
    with st.form("add_meal_form", clear_on_submit=True):
        new_meal = st.text_input("New meal name", placeholder="e.g. Pre-workout Snack")
        if st.form_submit_button("➕ Add Meal"):
            if new_meal.strip():
                st.session_state.diet_items.append(
                    {"meal": new_meal.strip(), "items": "", "calories": 0}
                )
                st.rerun()

    st.markdown("---")

    # ── Exercise Routine ──────────────────────────────────────────────────────
    st.markdown("### 🏋️ Exercise Routine")

    if "exercise_items" not in st.session_state:
        st.session_state.exercise_items = [
            {"name": "Push-ups",      "sets": 3, "reps": 15, "youtube_url": ""},
            {"name": "Squats",        "sets": 4, "reps": 12, "youtube_url": ""},
            {"name": "Plank",         "sets": 3, "reps": 60, "youtube_url": ""},
            {"name": "Jumping Jacks", "sets": 3, "reps": 30, "youtube_url": ""},
        ]

    exercise_routine = []
    for i, ex in enumerate(st.session_state.exercise_items):
        with st.container(border=True):
            col_name, col_sets, col_reps, col_del = st.columns([4, 1, 1, 1])
            with col_name:
                name_val = st.text_input(
                    "Exercise name",
                    value=ex["name"],
                    key=f"ex_name_val_{i}",
                )
            with col_sets:
                sets_val = st.number_input(
                    "Sets",
                    value=ex["sets"],
                    min_value=1, max_value=20,
                    key=f"ex_sets_val_{i}",
                )
            with col_reps:
                reps_val = st.number_input(
                    "Reps/Sec",
                    value=ex["reps"],
                    min_value=1, max_value=300,
                    key=f"ex_reps_val_{i}",
                )
            with col_del:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✕", key=f"del_ex_{i}", help="Remove this exercise"):
                    st.session_state.exercise_items.pop(i)
                    st.rerun()

            # YouTube link field — full width inside the card
            youtube_val = st.text_input(
                "▶ YouTube tutorial link (optional)",
                value=ex.get("youtube_url", ""),
                key=f"ex_yt_val_{i}",
                placeholder="e.g. https://www.youtube.com/watch?v=...",
            )

        exercise_routine.append({
            "name":        name_val,
            "sets":        sets_val,
            "reps":        reps_val,
            "youtube_url": youtube_val.strip(),
        })

    # Add custom exercise
    with st.form("add_exercise_form", clear_on_submit=True):
        new_ex = st.text_input("New exercise name", placeholder="e.g. Lunges")
        if st.form_submit_button("➕ Add Exercise"):
            if new_ex.strip():
                st.session_state.exercise_items.append(
                    {"name": new_ex.strip(), "sets": 3, "reps": 10, "youtube_url": ""}
                )
                st.rerun()

    st.markdown("---")

    # ── Publish ───────────────────────────────────────────────────────────────
    total_cal = sum(m["calories"] for m in diet_plan)
    st.markdown(
        f"**Plan Summary:** {len(diet_plan)} meals · "
        f"{total_cal} total kcal · {len(exercise_routine)} exercises"
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Publish Plan to All Clients",
                     use_container_width=True, type="primary"):
            if not any(m["items"] for m in diet_plan):
                st.error("Please add at least one food item to any meal.")
            elif not exercise_routine:
                st.error("Please add at least one exercise.")
            else:
                with st.spinner("Publishing…"):
                    plan_id = upsert_daily_plan(trainer_uid, diet_plan, exercise_routine)
                st.success(f"✅ Plan published! Your clients can now see it.")
                st.balloons()


# ─── TAB 2: CLIENT PROGRESS ──────────────────────────────────────────────────

def _client_progress_tab(trainer_uid: str):
    st.subheader("Today's Client Progress")
    st.caption(datetime.now().strftime("%A, %d %B %Y"))

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh"):
            st.rerun()

    clients  = get_trainer_clients(trainer_uid)
    statuses = get_all_client_statuses(trainer_uid)
    status_map = {s["clientUid"]: s for s in statuses}

    if not clients:
        st.warning(
            "No clients linked yet. Share your Trainer UID (shown at the top) "
            "with your clients so they can register under your account."
        )
        return

    # ── Summary metrics ───────────────────────────────────────────────────────
    total     = len(clients)
    submitted = sum(1 for c in clients if c["uid"] in status_map)
    pending   = total - submitted
    rate      = int((submitted / total) * 100) if total else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clients",   total)
    col2.metric("Submitted",       submitted)
    col3.metric("Pending",         pending)
    col4.metric("Completion Rate", f"{rate}%")

    st.markdown("---")

    # ── Per-client cards ──────────────────────────────────────────────────────
    for client in clients:
        uid    = client["uid"]
        name   = client["displayName"]
        email  = client["email"]
        status = status_map.get(uid)

        icon  = "✅" if status else "⏳"
        label = f"{icon} **{name}** — {email}"

        with st.expander(label, expanded=bool(status)):
            if not status:
                st.info("No submission yet for today.")
                continue

            col_tasks, col_remarks = st.columns(2)

            with col_tasks:
                st.markdown("**Completed Tasks:**")
                done = status.get("completedTasks", [])
                if done:
                    for task in done:
                        st.markdown(f"- ✅ {task}")
                else:
                    st.markdown("_No tasks marked complete_")

            with col_remarks:
                st.markdown("**Client Remarks:**")
                note = status.get("remarks", "").strip()
                if note:
                    st.info(f'"{note}"')
                else:
                    st.markdown("_No remarks submitted_")

            if status.get("submittedAt"):
                st.caption(f"Submitted at: {status['submittedAt']}")
