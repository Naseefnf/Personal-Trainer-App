"""
firebase_service.py
────────────────────────────────────────────────
All Firebase operations: Auth (REST API) + Firestore (Admin SDK).
No file/media logic — pure data sync only.
"""

import os
import requests
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# ─── FIREBASE ADMIN INIT ────────────────────────────────────────────────────

@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            # Try Streamlit Cloud secrets first
            if "firebase_service_account" in st.secrets:
                sa = dict(st.secrets["firebase_service_account"])
                sa["private_key"] = sa["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(sa)
            else:
                # Local fallback
                cred = credentials.Certificate("serviceAccountKey.json")
        except Exception as e:
            raise Exception(f"Firebase init failed: {e}")
        firebase_admin.initialize_app(cred)
    return firestore.client()


def get_db():
    return init_firebase()


# ─── AUTH (Firebase REST API) ────────────────────────────────────────────────

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyCt2ysSvXLlfohk43jExVM-n0A66S1scKs")


def sign_in(email: str, password: str) -> dict:
    """Authenticate a user with email and password."""
    url = (
        "https://identitytoolkit.googleapis.com/v1/"
        f"accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    )
    r = requests.post(url, json={
        "email": email,
        "password": password,
        "returnSecureToken": True,
    })
    data = r.json()
    if "error" in data:
        raise Exception(data["error"]["message"])
    return data  # contains localId, idToken, email


def sign_up(email: str, password: str) -> dict:
    """Register a new user with email and password."""
    url = (
        "https://identitytoolkit.googleapis.com/v1/"
        f"accounts:signUp?key={FIREBASE_API_KEY}"
    )
    r = requests.post(url, json={
        "email": email,
        "password": password,
        "returnSecureToken": True,
    })
    data = r.json()
    if "error" in data:
        raise Exception(data["error"]["message"])
    return data


# ─── USER DOCUMENTS ──────────────────────────────────────────────────────────

def create_user_doc(uid: str, email: str, display_name: str,
                    role: str, trainer_uid: str = None):
    """Create the Firestore user profile after registration."""
    get_db().collection("users").document(uid).set({
        "uid": uid,
        "email": email,
        "displayName": display_name,
        "role": role,               # "trainer" or "client"
        "trainerUid": trainer_uid,  # None for trainers
    })


def get_user_doc(uid: str) -> dict | None:
    """Fetch a user's Firestore profile by UID."""
    doc = get_db().collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def get_trainer_clients(trainer_uid: str) -> list:
    """Return all clients linked to a trainer."""
    docs = (
        get_db().collection("users")
        .where("trainerUid", "==", trainer_uid)
        .where("role", "==", "client")
        .stream()
    )
    return [d.to_dict() for d in docs]


# ─── DAILY PLANS ─────────────────────────────────────────────────────────────

def upsert_daily_plan(trainer_uid: str, diet_plan: list,
                      exercise_routine: list) -> str:
    """
    Trainer creates or overwrites today's plan.
    Document ID: {trainerUid}_{YYYY-MM-DD}
    """
    today = datetime.now().strftime("%Y-%m-%d")
    doc_id = f"{trainer_uid}_{today}"
    get_db().collection("daily_plans").document(doc_id).set({
        "trainerUid": trainer_uid,
        "date": today,
        "dietPlan": diet_plan,
        "exerciseRoutine": exercise_routine,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }, merge=True)
    return doc_id


def get_today_plan(trainer_uid: str) -> dict | None:
    """Client fetches trainer's plan for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    doc_id = f"{trainer_uid}_{today}"
    doc = get_db().collection("daily_plans").document(doc_id).get()
    return doc.to_dict() if doc.exists else None


# ─── CLIENT STATUS ────────────────────────────────────────────────────────────

def submit_client_status(client_uid: str, trainer_uid: str, plan_id: str,
                         completed_tasks: list, remarks: str):
    """
    Client submits (or updates) today's progress.
    Document ID: {clientUid}_{YYYY-MM-DD}
    """
    today = datetime.now().strftime("%Y-%m-%d")
    doc_id = f"{client_uid}_{today}"
    get_db().collection("client_status").document(doc_id).set({
        "clientUid": client_uid,
        "trainerUid": trainer_uid,
        "planId": plan_id,
        "date": today,
        "completedTasks": completed_tasks,
        "remarks": remarks,
        "submittedAt": firestore.SERVER_TIMESTAMP,
    }, merge=True)


def get_client_status(client_uid: str) -> dict | None:
    """Client fetches their own status for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    doc_id = f"{client_uid}_{today}"
    doc = get_db().collection("client_status").document(doc_id).get()
    return doc.to_dict() if doc.exists else None


def get_all_client_statuses(trainer_uid: str) -> list:
    """Trainer fetches all client submissions for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    docs = (
        get_db().collection("client_status")
        .where("trainerUid", "==", trainer_uid)
        .where("date", "==", today)
        .stream()
    )
    return [d.to_dict() for d in docs]
