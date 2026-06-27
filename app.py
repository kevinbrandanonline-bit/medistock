import os
from datetime import datetime
from flask import Flask, request, render_template_string, jsonify
import google.genai as genai

# ---------------- INVENTORY ---------------- #

inventory = {
    "Metformin":            {"stock": 18, "category": "Diabetes",          "otc": False, "expiry": "2026-08-15"},
    "Amlodipine":           {"stock": 14, "category": "Blood Pressure",    "otc": False, "expiry": "2027-01-10"},
    "Losartan":             {"stock": 16, "category": "Blood Pressure",    "otc": False, "expiry": "2026-11-20"},
    "Omeprazole":           {"stock": 20, "category": "Stomach",           "otc": True,  "expiry": "2026-08-01"},
    "Pantoprazole":         {"stock": 15, "category": "Stomach",           "otc": True,  "expiry": "2027-03-05"},
    "Diclofenac Gel":       {"stock": 12, "category": "Pain",              "otc": True,  "expiry": "2026-08-22"},
    "Hydrocortisone Cream": {"stock": 10, "category": "Skin Care",         "otc": True,  "expiry": "2026-12-31"},
    "Saline Nasal Drops":   {"stock": 18, "category": "Cold and Cough",    "otc": True,  "expiry": "2026-09-14"},
    "Vitamin D Tablets":    {"stock": 25, "category": "Supplements",       "otc": True,  "expiry": "2027-06-30"},
    "Iron Tablets":         {"stock": 22, "category": "Supplements",       "otc": True,  "expiry": "2026-10-18"},
    "Electrolyte Powder":   {"stock": 30, "category": "Hydration",         "otc": True,  "expiry": "2027-02-28"},
    "Antibiotic Ointment":  {"stock": 12, "category": "First Aid",         "otc": True,  "expiry": "2026-08-10"},
    "Pregnancy Test Kit":   {"stock": 10, "category": "Diagnostic",        "otc": True,  "expiry": "2026-08-30"},
    "Pulse Oximeter":       {"stock": 6,  "category": "Medical Equipment", "otc": False, "expiry": "2028-01-01"},
    "Steam Inhaler":        {"stock": 8,  "category": "Respiratory",       "otc": True,  "expiry": "2027-05-15"},
    "Anti-Dandruff Shampoo":{"stock": 14, "category": "Personal Care",     "otc": True,  "expiry": "2026-11-11"},
    "Antacid Syrup":        {"stock": 16, "category": "Stomach",           "otc": True,  "expiry": "2026-08-05"},
    "Lactase Tablets":      {"stock": 10, "category": "Digestive",         "otc": True,  "expiry": "2027-04-20"},
    "Antiseptic Wipes":     {"stock": 35, "category": "Hygiene",           "otc": True,  "expiry": "2026-09-01"},
    "Compression Bandage":  {"stock": 20, "category": "First Aid",         "otc": False, "expiry": "2028-06-15"},
    "Paracetamol":          {"stock": 20, "category": "Fever",             "otc": True,  "expiry": "2026-08-19"},
    "Ibuprofen":            {"stock": 12, "category": "Pain",              "otc": True,  "expiry": "2027-07-07"},
    "ORS":                  {"stock": 30, "category": "Hydration",         "otc": True,  "expiry": "2026-10-25"},
    "Bandage":              {"stock": 50, "category": "First Aid",         "otc": False, "expiry": "2029-01-01"},
}

PANEL_PASSWORD = "medistock@2026"

# ---------------- FLASK ---------------- #

app = Flask(__name__)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# ---------------- MAIN HTML TEMPLATE ---------------- #

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MediStock AI</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: 'Inter', Arial, sans-serif;
            background: #060d1f;
            color: white;
            min-height: 100vh;
            overflow-x: hidden;
        }
        .bg-orbs { position:fixed; inset:0; z-index:0; pointer-events:none; }
        .orb { position:absolute; border-radius:50%; filter:blur(80px); opacity:0.25; animation:float 10s ease-in-out infinite; }
        .orb1 { width:500px; height:500px; background:#22c55e; top:-100px; left:-150px; animation-delay:0s; }
        .orb2 { width:400px; height:400px; background:#3b82f6; bottom:-80px; right:-100px; animation-delay:3s; }
        .orb3 { width:300px; height:300px; background:#a855f7; top:40%; left:50%; animation-delay:6s; }
        @keyframes float {
            0%,100% { transform:translateY(0) scale(1); }
            50% { transform:translateY(-30px) scale(1.05); }
        }
        .grid-overlay {
            position:fixed; inset:0; z-index:0; pointer-events:none;
            background-image: linear-gradient(rgba(34,197,94,0.04) 1px,transparent 1px),
                              linear-gradient(90deg,rgba(34,197,94,0.04) 1px,transparent 1px);
            background-size:50px 50px;
        }
        .page-wrap {
            position:relative; z-index:1; min-height:100vh;
            display:flex; flex-direction:column; align-items:center;
            padding:40px 20px 60px;
        }

        /* NAVBAR */
        .navbar {
            width:100%; max-width:900px;
            display:flex; align-items:center; justify-content:space-between;
            margin-bottom:60px;
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:16px; padding:14px 24px;
            backdrop-filter:blur(10px);
            gap: 12px;
        }
        .nav-brand {
            display:flex; align-items:center; gap:10px;
            font-size:18px; font-weight:700; color:#22c55e;
        }
        .dot {
            width:8px; height:8px; background:#22c55e;
            border-radius:50%; animation:pulse 2s infinite;
        }
        @keyframes pulse {
            0%,100% { opacity:1; transform:scale(1); }
            50% { opacity:0.5; transform:scale(1.4); }
        }
        .nav-right { display:flex; align-items:center; gap:10px; }
        .nav-inv-btn {
            background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.3);
            color:#22c55e; padding:9px 18px; border-radius:10px;
            font-size:14px; font-weight:600; cursor:pointer; transition:.2s;
            text-decoration:none; display:inline-flex; align-items:center; gap:6px;
        }
        .nav-inv-btn:hover { background:rgba(34,197,94,0.25); transform:translateY(-1px); }

        /* STOCK PANEL BUTTON */
        .nav-stock-btn {
            background:linear-gradient(135deg,rgba(168,85,247,0.2),rgba(59,130,246,0.2));
            border:1px solid rgba(168,85,247,0.4);
            color:#c084fc; padding:9px 18px; border-radius:10px;
            font-size:14px; font-weight:600; cursor:pointer; transition:.2s;
            display:inline-flex; align-items:center; gap:6px;
            white-space:nowrap;
        }
        .nav-stock-btn:hover { background:rgba(168,85,247,0.25); transform:translateY(-1px); }

        /* HERO */
        .hero { text-align:center; margin-bottom:48px; max-width:700px; }
        .hero-badge {
            display:inline-flex; align-items:center; gap:8px;
            background:rgba(34,197,94,0.1); border:1px solid rgba(34,197,94,0.25);
            border-radius:999px; padding:6px 16px; font-size:13px;
            color:#86efac; margin-bottom:24px; font-weight:500;
        }
        .hero h1 {
            font-size:clamp(2.2rem,5vw,3.6rem); font-weight:800;
            line-height:1.15; margin-bottom:18px; letter-spacing:-1px;
        }
        .hero h1 .grad {
            background:linear-gradient(90deg,#22c55e,#3b82f6,#a855f7);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        }
        .hero p { color:#94a3b8; font-size:17px; line-height:1.7; max-width:560px; margin:0 auto; }

        /* STATS */
        .stats { display:flex; gap:16px; margin-bottom:40px; flex-wrap:wrap; justify-content:center; }
        .stat-card {
            background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
            border-radius:14px; padding:16px 26px; text-align:center;
            backdrop-filter:blur(8px); min-width:130px;
        }
        .stat-card .num { font-size:28px; font-weight:800; color:#22c55e; line-height:1; }
        .stat-card .lbl { font-size:12px; color:#64748b; margin-top:4px; font-weight:500; text-transform:uppercase; letter-spacing:.5px; }
        .stat-card.warn .num { color:#f59e0b; }
        .stat-card.danger .num { color:#ef4444; }

        /* EXPIRY BANNER */
        .expiry-banner {
            width:100%; max-width:900px;
            background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.3);
            border-radius:14px; padding:14px 22px; margin-bottom:32px;
            display:flex; align-items:center; gap:12px;
            font-size:15px; color:#fcd34d; font-weight:500;
        }

        /* MAIN CARD */
        .main-card {
            width:100%; max-width:900px;
            background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08);
            border-radius:24px; padding:40px;
            backdrop-filter:blur(20px); box-shadow:0 25px 60px rgba(0,0,0,0.5);
        }
        .section-label {
            font-size:11px; font-weight:700; text-transform:uppercase;
            letter-spacing:1.5px; color:#475569; margin-bottom:10px;
        }
        textarea {
            width:100%; height:140px; padding:18px;
            border:1.5px solid rgba(255,255,255,0.08); border-radius:14px;
            resize:none; font-size:16px; font-family:inherit;
            background:rgba(255,255,255,0.04); color:white;
            margin-bottom:20px; outline:none; transition:border .2s; line-height:1.6;
        }
        textarea:focus { border-color:#22c55e; }
        textarea::placeholder { color:#475569; }
        .btn-row { display:flex; gap:14px; }
        .btn-primary {
            flex:1; padding:16px; border:none; border-radius:14px;
            font-size:16px; font-weight:700; cursor:pointer; color:white;
            background:linear-gradient(135deg,#16a34a,#2563eb);
            transition:all .3s; font-family:inherit; position:relative; overflow:hidden;
        }
        .btn-primary::after {
            content:''; position:absolute; inset:0;
            background:linear-gradient(135deg,#22c55e,#3b82f6); opacity:0; transition:opacity .3s;
        }
        .btn-primary:hover::after { opacity:1; }
        .btn-primary span { position:relative; z-index:1; }
        .btn-primary:hover { transform:translateY(-2px); box-shadow:0 10px 30px rgba(34,197,94,0.3); }
        .btn-secondary {
            padding:16px 28px; border:1.5px solid rgba(255,255,255,0.12); border-radius:14px;
            font-size:16px; font-weight:600; cursor:pointer; color:#cbd5e1;
            background:rgba(255,255,255,0.05); transition:all .2s; font-family:inherit; white-space:nowrap;
        }
        .btn-secondary:hover { border-color:rgba(34,197,94,0.4); color:#22c55e; background:rgba(34,197,94,0.07); }
        .result { margin-top:32px; border-top:1px solid rgba(255,255,255,0.07); padding-top:28px; }
        .result-section { margin-bottom:22px; }
        .result-section .label {
            font-size:11px; font-weight:700; text-transform:uppercase;
            letter-spacing:1.5px; color:#475569; margin-bottom:10px;
        }
        .symptoms-box {
            background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07);
            border-radius:12px; padding:14px 18px; color:#cbd5e1; font-size:15px; line-height:1.6;
        }
        .ai-box {
            background:rgba(34,197,94,0.06); border:1px solid rgba(34,197,94,0.15);
            border-radius:12px; padding:18px; color:#e2e8f0; font-size:15px; line-height:1.8; white-space:pre-wrap;
        }
        .warning-note {
            display:flex; align-items:flex-start; gap:10px;
            background:rgba(251,191,36,0.07); border:1px solid rgba(251,191,36,0.2);
            border-radius:10px; padding:12px 16px; color:#fcd34d; font-size:13px; margin-top:16px; line-height:1.5;
        }
        .footer { margin-top:50px; color:#334155; font-size:13px; text-align:center; }

        /* ======== STOCK PANEL OVERLAY ======== */
        .overlay {
            display:flex; position:fixed; inset:0; z-index:100;
            background:rgba(0,0,0,0.7); backdrop-filter:blur(6px);
            align-items:center; justify-content:flex-end;
            visibility:hidden; opacity:0; pointer-events:none;
            transition:opacity .25s, visibility .25s;
        }
        .overlay.open { visibility:visible; opacity:1; pointer-events:all; }

        .panel {
            width:380px; height:100vh; overflow-y:auto;
            background:#0c1628; border-left:1px solid rgba(168,85,247,0.3);
            box-shadow:-20px 0 60px rgba(0,0,0,0.6);
            padding:30px 24px;
            animation:slideIn .3s ease;
        }
        @keyframes slideIn {
            from { transform:translateX(100%); opacity:0; }
            to   { transform:translateX(0);    opacity:1; }
        }
        .panel-header {
            display:flex; align-items:center; justify-content:space-between;
            margin-bottom:24px;
        }
        .panel-title {
            font-size:18px; font-weight:700;
            background:linear-gradient(90deg,#c084fc,#818cf8);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        }
        .panel-close {
            background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.1);
            color:#94a3b8; width:32px; height:32px; border-radius:8px;
            font-size:16px; cursor:pointer; display:flex; align-items:center; justify-content:center;
            transition:.2s;
        }
        .panel-close:hover { background:rgba(239,68,68,0.2); color:#f87171; border-color:rgba(239,68,68,0.3); }

        /* Password gate */
        .pw-gate { display:block; }
        .pw-gate p { color:#94a3b8; font-size:14px; line-height:1.6; margin-bottom:14px; }
        .pw-gate .pw-input { margin-bottom:10px; }
        .pw-gate .pw-error { margin-bottom:10px; }
        .pw-input {
            width:100%; padding:13px 16px;
            background:rgba(255,255,255,0.05); border:1.5px solid rgba(255,255,255,0.1);
            border-radius:12px; color:white; font-size:15px; font-family:inherit; outline:none; transition:border .2s;
        }
        .pw-input:focus { border-color:#c084fc; }
        .pw-input::placeholder { color:#475569; }
        .pw-btn {
            padding:13px; background:linear-gradient(135deg,#7c3aed,#2563eb);
            border:none; border-radius:12px; color:white; font-size:15px;
            font-weight:700; cursor:pointer; font-family:inherit; transition:.2s;
        }
        .pw-btn:hover { opacity:.9; transform:translateY(-1px); }
        .pw-error { color:#f87171; font-size:13px; display:none; }

        /* Panel content (after unlock) */
        .panel-content { display:none; flex-direction:column; gap:20px; width:100%; }

        .panel-search {
            width:100%; padding:11px 14px;
            background:rgba(255,255,255,0.05); border:1.5px solid rgba(255,255,255,0.08);
            border-radius:10px; color:white; font-size:14px; font-family:inherit; outline:none; transition:border .2s;
        }
        .panel-search:focus { border-color:#c084fc; }
        .panel-search::placeholder { color:#475569; }

        .med-list { display:flex; flex-direction:column; gap:10px; max-height:60vh; overflow-y:auto; padding-right:4px; }
        .med-list::-webkit-scrollbar { width:4px; }
        .med-list::-webkit-scrollbar-track { background:transparent; }
        .med-list::-webkit-scrollbar-thumb { background:#334155; border-radius:4px; }

        .med-item {
            background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07);
            border-radius:12px; padding:14px;
            display:flex; flex-direction:column; gap:10px;
            transition:.2s;
        }
        .med-item:hover { border-color:rgba(168,85,247,0.3); background:rgba(168,85,247,0.05); }
        .med-item-top { display:flex; align-items:center; justify-content:space-between; }
        .med-name { font-size:14px; font-weight:600; color:#e2e8f0; }
        .med-stock-badge {
            font-size:12px; font-weight:700; padding:3px 10px; border-radius:999px;
        }
        .badge-ok  { background:rgba(34,197,94,0.15);  color:#22c55e; }
        .badge-low { background:rgba(239,68,68,0.15);  color:#ef4444; }
        .med-cat { font-size:11px; color:#475569; }

        .med-controls { display:flex; align-items:center; gap:8px; }
        .qty-btn {
            width:32px; height:32px; border-radius:8px; border:none;
            font-size:18px; font-weight:700; cursor:pointer; transition:.15s;
            display:flex; align-items:center; justify-content:center;
        }
        .qty-btn.minus { background:rgba(239,68,68,0.15); color:#f87171; }
        .qty-btn.minus:hover { background:rgba(239,68,68,0.3); }
        .qty-btn.plus  { background:rgba(34,197,94,0.15);  color:#22c55e; }
        .qty-btn.plus:hover  { background:rgba(34,197,94,0.3); }
        .qty-input {
            flex:1; text-align:center; padding:7px;
            background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1);
            border-radius:8px; color:white; font-size:14px; font-weight:600; font-family:inherit; outline:none;
        }
        .qty-input:focus { border-color:#c084fc; }
        .action-btn {
            width:100%; padding:9px; border:none; border-radius:9px;
            font-size:13px; font-weight:700; cursor:pointer; font-family:inherit; transition:.2s;
        }
        .action-deposit {
            background:rgba(34,197,94,0.15); color:#22c55e; border:1px solid rgba(34,197,94,0.3);
        }
        .action-deposit:hover { background:rgba(34,197,94,0.3); }
        .action-take {
            background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.25);
        }
        .action-take:hover { background:rgba(239,68,68,0.25); }

        .toast {
            position:fixed; bottom:30px; right:30px; z-index:999;
            background:#1e293b; border:1px solid rgba(34,197,94,0.3);
            border-radius:12px; padding:14px 20px;
            font-size:14px; color:#86efac; font-weight:500;
            box-shadow:0 8px 30px rgba(0,0,0,0.4);
            transform:translateY(20px); opacity:0;
            transition:all .3s;
        }
        .toast.show { transform:translateY(0); opacity:1; }
        .toast.error { border-color:rgba(239,68,68,0.3); color:#f87171; }

        .panel-footer-note {
            color:#334155; font-size:12px; text-align:center; margin-top:10px; line-height:1.5;
        }
    </style>
</head>
<body>

<div class="bg-orbs">
    <div class="orb orb1"></div>
    <div class="orb orb2"></div>
    <div class="orb orb3"></div>
</div>
<div class="grid-overlay"></div>

<!-- STOCK PANEL OVERLAY -->
<div class="overlay" id="stockOverlay" onclick="closeOnOverlay(event)">
    <div class="panel" id="stockPanel">
        <div class="panel-header">
            <div class="panel-title">💊 Stock Manager</div>
            <button class="panel-close" onclick="closePanel()">✕</button>
        </div>

        <!-- Password gate -->
        <div class="pw-gate" id="pwGate">
            <p>🔐 This panel is restricted.<br>Enter the password to continue.</p>
            <input class="pw-input" type="password" id="pwInput" placeholder="Enter password..."
                onkeydown="if(event.key==='Enter') checkPassword()" />
            <div class="pw-error" id="pwError">❌ Incorrect password. Try again.</div>
            <button class="pw-btn" onclick="checkPassword()">🔓 Unlock Panel</button>
        </div>

        <!-- Panel content -->
        <div class="panel-content" id="panelContent">
            <input class="panel-search" type="text" placeholder="🔍 Search medicine..."
                oninput="filterPanel(this.value)" />
            <div class="med-list" id="medList">
                <!-- Filled by JS -->
            </div>
            <p class="panel-footer-note">Changes are live in memory.<br>Restart server to reset.</p>
        </div>
    </div>
</div>

<!-- TOAST -->
<div class="toast" id="toast"></div>

<div class="page-wrap">

    <!-- Navbar -->
    <nav class="navbar">
        <div class="nav-brand">
            <div class="dot"></div>
            MediStock AI
        </div>
        <div class="nav-right">
            <button class="nav-stock-btn" onclick="openPanel()">
                💉 Take / Deposit
            </button>
            <a class="nav-inv-btn" href="/inventory">📦 Inventory</a>
        </div>
    </nav>

    <!-- Hero -->
    <div class="hero">
        <div class="hero-badge">
            <span>🟢</span> AI-Powered · Real-Time Inventory
        </div>
        <h1>Your Smart <span class="grad">Pharmacy</span><br>Assistant</h1>
        <p>Describe your symptoms and instantly get medicine recommendations from live inventory — powered by Gemini AI.</p>
    </div>

    <!-- Stats -->
    <div class="stats">
        <div class="stat-card">
            <div class="num" id="statTotal">{{ total }}</div>
            <div class="lbl">Medicines</div>
        </div>
        <div class="stat-card warn">
            <div class="num">{{ expiring_soon }}</div>
            <div class="lbl">Expiring This Month</div>
        </div>
        <div class="stat-card danger">
            <div class="num" id="statLow">{{ low_stock }}</div>
            <div class="lbl">Low Stock</div>
        </div>
        <div class="stat-card">
            <div class="num">{{ otc_count }}</div>
            <div class="lbl">OTC Available</div>
        </div>
    </div>

    {% if expiring_soon > 0 %}
    <div class="expiry-banner">
        <span>📅</span>
        ⚠ {{ expiring_soon }} medicine{{ 's' if expiring_soon != 1 else '' }} expiring this month — check inventory for details.
    </div>
    {% endif %}

    <!-- Main card -->
    <div class="main-card">
        <p class="section-label">Describe Symptoms</p>
        <form action="/analyze" method="POST">
            <textarea name="symptoms"
                placeholder="e.g. I have a headache, mild fever, and sore throat since yesterday..."
                required>{{ symptoms if symptoms }}</textarea>
            <div class="btn-row">
                <button class="btn-primary" type="submit">
                    <span>🧠 Analyze Symptoms</span>
                </button>
                <button class="btn-secondary" type="button"
                    onclick="window.location.href='/inventory'">
                    📦 Inventory
                </button>
            </div>
        </form>

        {% if result %}
        <div class="result">
            <div class="result-section">
                <div class="label">Your Symptoms</div>
                <div class="symptoms-box">{{ symptoms }}</div>
            </div>
            <div class="result-section">
                <div class="label">🤖 AI Recommendation</div>
                <div class="ai-box">{{ result }}</div>
            </div>
            <div class="warning-note">
                ⚠ This AI provides educational information only and is not a substitute for professional medical advice.
            </div>
        </div>
        {% endif %}
    </div>

    <div class="footer">© 2026 MediStock AI · Powered by Gemini</div>
</div>

<script>
// ---- Inventory data from server ----
let inv = {{ inv_json | safe }};

// ---- Panel open/close ----
let unlocked = false;

function openPanel() {
    document.getElementById('stockOverlay').classList.add('open');
    document.getElementById('pwInput').value = '';
    document.getElementById('pwError').style.display = 'none';
    if (!unlocked) {
        document.getElementById('pwGate').style.display = 'flex';
        document.getElementById('panelContent').style.display = 'none';
        setTimeout(() => document.getElementById('pwInput').focus(), 100);
    }
}

function closePanel() {
    document.getElementById('stockOverlay').classList.remove('open');
}

function closeOnOverlay(e) {
    if (e.target === document.getElementById('stockOverlay')) closePanel();
}

// ---- Password check ----
function checkPassword() {
    const val = document.getElementById('pwInput').value;
    fetch('/check_password', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({password: val})
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            unlocked = true;
            document.getElementById('pwGate').style.display = 'none';
            document.getElementById('panelContent').style.display = 'block';
            renderMedList(inv);
        } else {
            document.getElementById('pwError').style.display = 'block';
        }
    });
}

// ---- Render medicine list ----
function renderMedList(data, filter='') {
    const list = document.getElementById('medList');
    list.innerHTML = '';
    const keys = Object.keys(data).filter(k => k.toLowerCase().includes(filter.toLowerCase()));
    if (keys.length === 0) {
        list.innerHTML = '<p style="color:#475569;text-align:center;font-size:14px;padding:20px;">No medicines found.</p>';
        return;
    }
    keys.forEach(med => {
        const info = data[med];
        const badgeClass = info.stock <= 10 ? 'badge-low' : 'badge-ok';
        const div = document.createElement('div');
        div.className = 'med-item';
        div.id = 'item-' + med.replace(/\\s+/g,'_');
        div.innerHTML = `
            <div class="med-item-top">
                <div>
                    <div class="med-name">${med}</div>
                    <div class="med-cat">${info.category}</div>
                </div>
                <span class="med-stock-badge ${badgeClass}" id="badge-${med.replace(/\\s+/g,'_')}">
                    ${info.stock} left
                </span>
            </div>
            <div class="med-controls">
                <button class="qty-btn minus" onclick="changeQty('${med}',-1)">−</button>
                <input class="qty-input" type="number" min="1" value="1" id="qty-${med.replace(/\\s+/g,'_')}" />
                <button class="qty-btn plus"  onclick="changeQty('${med}',1)">+</button>
            </div>
            <button class="action-btn action-deposit" onclick="updateStock('${med}','deposit')">
                ➕ Deposit Stock
            </button>
            <button class="action-btn action-take" onclick="updateStock('${med}','take')">
                ➖ Take / Dispense
            </button>
        `;
        list.appendChild(div);
    });
}

function filterPanel(val) {
    renderMedList(inv, val);
}

// ---- Update stock ----
function changeQty(med, delta) {
    const id = 'qty-' + med.replace(/\\s+/g,'_');
    const input = document.getElementById(id);
    let val = parseInt(input.value) || 1;
    val = Math.max(1, val + delta);
    input.value = val;
}

function updateStock(med, action) {
    const qtyId = 'qty-' + med.replace(/\\s+/g,'_');
    const qty = parseInt(document.getElementById(qtyId)?.value) || 1;

    fetch('/update_stock', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({medicine: med, action: action, qty: qty})
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            inv[med].stock = data.new_stock;
            const badgeId = 'badge-' + med.replace(/\\s+/g,'_');
            const badge = document.getElementById(badgeId);
            if (badge) {
                badge.textContent = data.new_stock + ' left';
                badge.className = 'med-stock-badge ' + (data.new_stock <= 10 ? 'badge-low' : 'badge-ok');
            }
            const icon = action === 'deposit' ? '✅' : '💊';
            const verb = action === 'deposit' ? 'Deposited' : 'Dispensed';
            showToast(`${icon} ${verb} ${qty} × ${med}. Stock: ${data.new_stock}`, false);
        } else {
            showToast('❌ ' + data.error, true);
        }
    });
}

// ---- Toast ----
function showToast(msg, isError=false) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast' + (isError ? ' error' : '');
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
}

// Keyboard shortcut: Escape to close
document.addEventListener('keydown', e => { if (e.key === 'Escape') closePanel(); });
</script>

</body>
</html>
"""

# ---------------- HELPERS ---------------- #

def get_stats():
    now = datetime.now()
    expiring_soon = sum(
        1 for info in inventory.values()
        if datetime.strptime(info["expiry"], "%Y-%m-%d").year == now.year
        and datetime.strptime(info["expiry"], "%Y-%m-%d").month == now.month
    )
    low_stock  = sum(1 for info in inventory.values() if info["stock"] <= 10)
    otc_count  = sum(1 for info in inventory.values() if info["otc"])
    return expiring_soon, low_stock, otc_count

import json

def inv_json():
    return json.dumps({k: {"stock": v["stock"], "category": v["category"]} for k, v in inventory.items()})

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    expiring_soon, low_stock, otc_count = get_stats()
    return render_template_string(HTML,
        symptoms="", result=None,
        total=len(inventory),
        expiring_soon=expiring_soon,
        low_stock=low_stock,
        otc_count=otc_count,
        inv_json=inv_json()
    )

@app.route("/check_password", methods=["POST"])
def check_password():
    data = request.get_json()
    return jsonify({"ok": data.get("password") == PANEL_PASSWORD})

@app.route("/update_stock", methods=["POST"])
def update_stock():
    data = request.get_json()
    med    = data.get("medicine")
    action = data.get("action")
    qty    = int(data.get("qty", 1))

    if med not in inventory:
        return jsonify({"ok": False, "error": "Medicine not found."})
    if qty < 1:
        return jsonify({"ok": False, "error": "Quantity must be at least 1."})

    current = inventory[med]["stock"]
    if action == "deposit":
        inventory[med]["stock"] = current + qty
    elif action == "take":
        if qty > current:
            return jsonify({"ok": False, "error": f"Only {current} in stock."})
        inventory[med]["stock"] = current - qty
    else:
        return jsonify({"ok": False, "error": "Invalid action."})

    return jsonify({"ok": True, "new_stock": inventory[med]["stock"]})

@app.route("/inventory")
def show_inventory():
    total = len(inventory)
    now = datetime.now()

    expiring_this_month = []
    rows = ""
    for med, info in inventory.items():
        stock = info["stock"]
        expiry_date = datetime.strptime(info["expiry"], "%Y-%m-%d")
        days_left = (expiry_date - now).days
        stock_color = "#ef4444" if stock <= 10 else "#22c55e"

        if expiry_date.year == now.year and expiry_date.month == now.month:
            expiring_this_month.append(med)
            expiry_style = "color:#f59e0b;font-weight:bold;"
            expiry_icon = "⚠ "
        elif days_left < 0:
            expiry_style = "color:#ef4444;font-weight:bold;"
            expiry_icon = "❌ "
        elif days_left <= 90:
            expiry_style = "color:#fb923c;font-weight:bold;"
            expiry_icon = "🔶 "
        else:
            expiry_style = "color:#86efac;"
            expiry_icon = ""

        med_id = med.replace(' ', '_').replace('-', '_')
        rows += f"""
            <tr class="med-row" id="row-{med_id}">
                <td>{med}</td>
                <td>
                    <div class="stock-ctrl">
                        <button class="sb minus" onclick="adjStock('{med}', 'take')">−</button>
                        <span class="stock-num" id="stk-{med_id}" style="color:{stock_color};">{stock}</span>
                        <button class="sb plus" onclick="adjStock('{med}', 'deposit')">+</button>
                    </div>
                </td>
                <td>{info['category']}</td>
                <td>{'✅ Yes' if info['otc'] else '❌ No'}</td>
                <td style='{expiry_style}'>{expiry_icon}{info['expiry']}</td>
            </tr>
        """

    expiry_banner = ""
    if expiring_this_month:
        count = len(expiring_this_month)
        expiry_banner = f"""
        <div class="expiry-banner">
            <span>📅</span>
            ⚠ {count} medicine{'s' if count != 1 else ''} expiring this month:
            <strong style="margin-left:6px;">{', '.join(expiring_this_month)}</strong>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MediStock Inventory</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
            * {{ margin:0;padding:0;box-sizing:border-box; }}
            body {{ font-family:'Inter',Arial,sans-serif; background:#060d1f; color:white; min-height:100vh; overflow-x:hidden; }}
            .bg-orbs {{ position:fixed;inset:0;z-index:0;pointer-events:none; }}
            .orb {{ position:absolute;border-radius:50%;filter:blur(80px);opacity:0.2; }}
            .orb1 {{ width:500px;height:500px;background:#22c55e;top:-100px;left:-150px; }}
            .orb2 {{ width:400px;height:400px;background:#3b82f6;bottom:-80px;right:-100px; }}
            .grid-overlay {{
                position:fixed;inset:0;z-index:0;pointer-events:none;
                background-image:linear-gradient(rgba(34,197,94,0.03) 1px,transparent 1px),
                                 linear-gradient(90deg,rgba(34,197,94,0.03) 1px,transparent 1px);
                background-size:50px 50px;
            }}
            .page-wrap {{ position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:40px 20px 60px; }}
            .navbar {{
                display:flex;align-items:center;justify-content:space-between;
                background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                border-radius:16px;padding:14px 24px;margin-bottom:40px;backdrop-filter:blur(10px);
            }}
            .nav-brand {{ font-size:18px;font-weight:700;color:#22c55e;display:flex;align-items:center;gap:10px; }}
            .dot {{ width:8px;height:8px;background:#22c55e;border-radius:50%; }}
            .back-btn {{
                color:#22c55e;text-decoration:none;font-size:14px;font-weight:600;
                border:1px solid rgba(34,197,94,0.3);padding:8px 18px;border-radius:10px;
                background:rgba(34,197,94,0.08);transition:.2s;
            }}
            .back-btn:hover {{ background:rgba(34,197,94,0.2); }}
            h1 {{
                font-size:2.2rem;font-weight:800;
                background:linear-gradient(90deg,#22c55e,#3b82f6);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px;
            }}
            .subtitle {{ color:#64748b;font-size:14px;margin-bottom:24px; }}
            .stats {{ display:flex;gap:14px;margin-bottom:28px;flex-wrap:wrap; }}
            .stat-card {{
                background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                border-radius:12px;padding:14px 22px;text-align:center;min-width:120px;
            }}
            .stat-card .num {{ font-size:24px;font-weight:800;color:#22c55e; }}
            .stat-card .lbl {{ font-size:11px;color:#64748b;margin-top:3px;text-transform:uppercase;letter-spacing:.5px; }}
            .stat-card.warn .num {{ color:#f59e0b; }}
            .stat-card.danger .num {{ color:#ef4444; }}
            .expiry-banner {{
                background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);
                border-radius:14px;padding:14px 20px;margin-bottom:24px;
                display:flex;align-items:flex-start;gap:10px;color:#fcd34d;font-size:14px;font-weight:500;
            }}
            .search-wrap {{ position:relative;margin-bottom:20px; }}
            .search-icon {{ position:absolute;left:14px;top:50%;transform:translateY(-50%);font-size:16px; }}
            #searchInput {{
                width:100%;padding:13px 14px 13px 42px;
                border:1.5px solid rgba(255,255,255,0.08);border-radius:12px;
                background:rgba(255,255,255,0.04);color:white;font-size:15px;font-family:inherit;outline:none;transition:border .2s;
            }}
            #searchInput:focus {{ border-color:#22c55e; }}
            #searchInput::placeholder {{ color:#475569; }}
            .table-wrap {{
                background:rgba(15,23,42,0.7);border-radius:18px;overflow:hidden;
                box-shadow:0 10px 40px rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.06);
            }}
            table {{ width:100%;border-collapse:collapse; }}
            th {{
                background:linear-gradient(90deg,#064e3b,#1e3a8a);
                color:white;padding:15px 16px;text-align:center;
                font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
            }}
            td {{ padding:13px 16px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.04);font-size:14px; }}
            tr.med-row:hover td {{ background:rgba(255,255,255,0.04); }}
            #noResult {{ display:none;text-align:center;padding:30px;color:#475569;font-size:15px; }}
            .legend {{ margin-top:18px;display:flex;gap:20px;flex-wrap:wrap;font-size:12px;color:#475569; }}
            .stock-ctrl {{ display:inline-flex;align-items:center;gap:8px; }}
            .stock-num {{ font-size:15px;font-weight:700;min-width:28px;text-align:center;display:inline-block; }}
            .sb {{
                width:28px;height:28px;border:none;border-radius:7px;
                font-size:17px;font-weight:700;cursor:pointer;
                display:inline-flex;align-items:center;justify-content:center;
                line-height:1;transition:.15s;
            }}
            .sb.minus {{ background:rgba(239,68,68,0.18);color:#f87171; }}
            .sb.minus:hover {{ background:rgba(239,68,68,0.35); }}
            .sb.plus  {{ background:rgba(34,197,94,0.18);color:#4ade80; }}
            .sb.plus:hover  {{ background:rgba(34,197,94,0.35); }}
            .inv-toast {{
                position:fixed;bottom:28px;right:28px;z-index:999;
                background:#1e293b;border:1px solid rgba(34,197,94,0.35);
                border-radius:12px;padding:13px 20px;font-size:14px;color:#86efac;
                font-weight:500;box-shadow:0 8px 30px rgba(0,0,0,0.5);
                transform:translateY(16px);opacity:0;transition:all .3s;pointer-events:none;
            }}
            .inv-toast.show {{ transform:translateY(0);opacity:1; }}
            .inv-toast.err  {{ border-color:rgba(239,68,68,0.35);color:#f87171; }}
        </style>
    </head>
    <body>
        <div class="bg-orbs"><div class="orb orb1"></div><div class="orb orb2"></div></div>
        <div class="grid-overlay"></div>
        <div class="page-wrap">
            <nav class="navbar">
                <div class="nav-brand"><div class="dot"></div> MediStock AI</div>
                <a class="back-btn" href="/">⬅ Back to Home</a>
            </nav>
            <h1>📦 Inventory Dashboard</h1>
            <p class="subtitle">Live stock and expiry overview for all medicines</p>
            <div class="stats">
                <div class="stat-card"><div class="num">{total}</div><div class="lbl">Total</div></div>
                <div class="stat-card warn"><div class="num">{len(expiring_this_month)}</div><div class="lbl">Expiring This Month</div></div>
                <div class="stat-card danger"><div class="num">{sum(1 for i in inventory.values() if i['stock'] <= 10)}</div><div class="lbl">Low Stock</div></div>
            </div>
            {expiry_banner}
            <div class="search-wrap">
                <span class="search-icon">🔍</span>
                <input type="text" id="searchInput" placeholder="Search by name, category, OTC..." oninput="filterTable()" />
            </div>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Medicine</th><th>Qty Left</th><th>Category</th><th>OTC</th><th>📅 Expiry</th>
                        </tr>
                    </thead>
                    <tbody id="medTable">{rows}</tbody>
                </table>
                <div id="noResult">😕 No medicines found.</div>
            </div>
            <div class="legend">
                <span>🟢 In Stock &nbsp; 🔴 Low (≤10)</span>
                <span>⚠ Expiring this month &nbsp; 🔶 Within 90 days &nbsp; ❌ Expired</span>
            </div>
        </div>
        <div class="inv-toast" id="invToast"></div>
        <script>
            function filterTable() {{
                const q = document.getElementById("searchInput").value.toLowerCase();
                const rows = document.querySelectorAll(".med-row");
                let vis = 0;
                rows.forEach(r => {{
                    if (r.innerText.toLowerCase().includes(q)) {{ r.style.display=""; vis++; }}
                    else r.style.display="none";
                }});
                document.getElementById("noResult").style.display = vis===0?"block":"none";
            }}

            function adjStock(med, action) {{
                fetch('/update_stock', {{
                    method: 'POST',
                    headers: {{'Content-Type':'application/json'}},
                    body: JSON.stringify({{medicine: med, action: action, qty: 1}})
                }})
                .then(r => r.json())
                .then(data => {{
                    if (data.ok) {{
                        const id = med.replace(/ /g,'_').replace(/-/g,'_');
                        const el = document.getElementById('stk-' + id);
                        if (el) {{
                            el.textContent = data.new_stock;
                            el.style.color = data.new_stock <= 10 ? '#ef4444' : '#22c55e';
                        }}
                        const verb = action === 'deposit' ? '➕ Added 1' : '➖ Removed 1';
                        showToast(verb + ' · ' + med + ' → ' + data.new_stock + ' left', false);
                    }} else {{
                        showToast('❌ ' + data.error, true);
                    }}
                }})
                .catch(() => showToast('❌ Network error', true));
            }}

            function showToast(msg, err) {{
                const t = document.getElementById('invToast');
                t.textContent = msg;
                t.className = 'inv-toast' + (err ? ' err' : '');
                t.classList.add('show');
                setTimeout(() => t.classList.remove('show'), 2800);
            }}
        </script>
    </body>
    </html>
    """
    return html

@app.route("/analyze", methods=["POST"])
def analyze():
    symptoms = request.form["symptoms"]
    inventory_text = ""
    for medicine, info in inventory.items():
        inventory_text += (
            f"{medicine} | Stock: {info['stock']} | "
            f"Category: {info['category']} | OTC: {info['otc']} | "
            f"Expiry: {info['expiry']}\n"
        )

    prompt = f"""
You are MediStock AI. You are NOT a doctor. You are an AI assistant that helps pharmacists.

Patient Symptoms: {symptoms}

Current Pharmacy Inventory:
{inventory_text}

Rules:
1. Never diagnose diseases.
2. Only recommend medicines that exist in the inventory.
3. Never recommend medicines whose stock is 0.
4. Mention the available stock.
5. Do not recommend medicines expiring within 7 days.
6. For emergencies (chest pain, difficulty breathing, severe bleeding, loss of consciousness, very high fever, seizures): advise hospital immediately, no medicine recommendations.
7. Keep under 120 words.
8. Finish with: ⚠ This is not a diagnosis. Please consult a qualified healthcare professional.
"""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        result = response.text
    except Exception as e:
        result = f"❌ Gemini Error:\n{e}"

    expiring_soon, low_stock, otc_count = get_stats()
    return render_template_string(HTML,
        symptoms=symptoms, result=result,
        total=len(inventory),
        expiring_soon=expiring_soon,
        low_stock=low_stock,
        otc_count=otc_count,
        inv_json=inv_json()
    )

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
