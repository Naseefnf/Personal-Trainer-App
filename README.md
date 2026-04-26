# 💪 Trainer-Client Sync

A real-time web app for trainers to publish daily workout and diet plans,
and for clients to track completion and send remarks — built with Streamlit + Firebase.

---

## 🗂️ Project Structure

```
trainer_client_sync/
├── app.py                  ← Entry point (run this)
├── auth.py                 ← Login & Registration
├── trainer_view.py         ← Trainer dashboard
├── client_view.py          ← Client dashboard
├── firebase_service.py     ← All Firebase operations
├── requirements.txt        ← Python dependencies
├── serviceAccountKey.json  ← YOUR Firebase key (you create this)
└── .streamlit/
    └── config.toml         ← App theme
```

---

## ⚙️ Setup Instructions (Ubuntu)

### Step 1 — Install Python & pip (if not already installed)
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### Step 2 — Create a virtual environment
```bash
cd trainer_client_sync
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up Firebase

1. Go to https://console.firebase.google.com
2. Create a new project (e.g. "trainer-client-sync")
3. Enable **Authentication** → Sign-in method → **Email/Password** → Enable
4. Enable **Firestore Database** → Start in Test Mode
5. Go to Project Settings → Service Accounts → **Generate new private key**
   → Download the JSON file → rename it to `serviceAccountKey.json`
   → place it in the project root folder
6. Go to Project Settings → General → Your apps → **Web app** → Register app
   → Copy the `apiKey` value

### Step 5 — Set your Firebase API Key

Open `firebase_service.py` and replace this line:
```python
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "YOUR_FIREBASE_WEB_API_KEY")
```
Either:
- Replace `YOUR_FIREBASE_WEB_API_KEY` directly with your actual key, OR
- Set it as an environment variable:
  ```bash
  export FIREBASE_API_KEY="AIzaSy..."
  ```

### Step 6 — Add Firestore Security Rules (optional but recommended)

In Firebase Console → Firestore → Rules, paste:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{uid} {
      allow read, write: if request.auth.uid == uid;
    }
    match /daily_plans/{planId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
    match /client_status/{statusId} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### Step 7 — Run the app
```bash
streamlit run app.py
```

The app opens automatically at: **http://localhost:8501**

---

## 👤 How to Use

### Trainer Flow
1. Register with role = **Trainer**
2. Copy your **Trainer UID** shown on your dashboard
3. Share it with your clients
4. Go to "Upload Today's Plan" tab → add meals + exercises → click **Publish**
5. Go to "Client Progress" tab → see who submitted and read their remarks

### Client Flow
1. Register with role = **Client** → paste your trainer's UID
2. Login → see today's plan immediately after trainer publishes
3. Tick off completed meals and exercises
4. Write any remarks in the text box
5. Click **Submit Progress** → trainer sees it instantly

---

## 🌐 Deploy Online (Free) — Streamlit Cloud

1. Push this project to a GitHub repository
2. Go to https://streamlit.io/cloud → Sign in with GitHub
3. Click **New App** → select your repo → set main file to `app.py`
4. In **Secrets** (gear icon), add:
   ```toml
   FIREBASE_API_KEY = "your_api_key_here"
   ```
5. Upload `serviceAccountKey.json` as a secret file OR paste its contents as:
   ```toml
   [firebase]
   type = "service_account"
   project_id = "..."
   # ... rest of the JSON fields
   ```
6. Click **Deploy** — you get a free public URL like:
   `https://yourname-trainer-sync.streamlit.app`

Share that URL with your trainer and clients — no APK, no installation.

---

## 🔥 Firestore Data Schema

```
users/{userId}
  uid, email, displayName, role, trainerUid

daily_plans/{trainerUid_YYYY-MM-DD}
  trainerUid, date, dietPlan[], exerciseRoutine[], updatedAt

client_status/{clientUid_YYYY-MM-DD}
  clientUid, trainerUid, planId, date
  completedTasks[], remarks, submittedAt
```
