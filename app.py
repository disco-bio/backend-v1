from flask import Flask, redirect, request, url_for, session, render_template
from flask_session import Session

from oauthlib.oauth2 import WebApplicationClient
import requests

from dotenv import load_dotenv
import os
import json

load_dotenv()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"]='1'

GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = (
		"https://accounts.google.com/.well-known/openid-configuration"
		)


client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
	return requests.get(GOOGLE_DISCOVERY_URL).json()

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# app.config.update(dict(
#   PREFERRED_URL_SCHEME = 'https'
# ))

app.secret_key = os.urandom(24)

@app.route("/")
def index():
	if not session.get("email"):
		return render_template("index.html")
		# return '<a href="/login">Login</a>'
	else:
		return session["email"]

@app.route("/login")
def login():
	google_provider_cfg = get_google_provider_cfg()
	auth_endpoint = google_provider_cfg["authorization_endpoint"]

	# BASE_URL = "https://www.trydisco.net/login"

	BASE_URL = request.base_url
	BASE_URL.replace("https", "http")
	BASE_URL.replace("http", "https")

	print("redirect_uri", BASE_URL+"/callback")

	request_uri = client.prepare_request_uri(
		auth_endpoint,
		redirect_uri = BASE_URL + "/callback",
		# redirect_uri="https://www.trydisco.net/login/callback"
		# redirect_uri = request.base_url + "/callback",
		scope = ["openid", "email", "profile"]
		)
	return redirect(request_uri)

@app.route("/login/callback")
def callback():
	code = request.args.get("code")
	google_provider_cfg = get_google_provider_cfg()
	token_endpoint = google_provider_cfg["token_endpoint"]

	print("redirect_url", request.base_url)

	token_url, headers, body = client.prepare_token_request(
		token_endpoint,
		authorization_response=request.url,
		redirect_url=request.base_url,
		code=code
		)
	token_response = requests.post(
		token_url,
		headers=headers,
		data=body,
		auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
		)
	client.parse_request_body_response(json.dumps(token_response.json()))

	userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
	uri, headers, body = client.add_token(userinfo_endpoint)
	userinfo_response = requests.get(uri, headers=headers, data=body)

	if userinfo_response.json().get("email_verified"):
		unique_id = userinfo_response.json()["sub"]
		users_email = userinfo_response.json()["email"]
		users_name = userinfo_response.json()["given_name"]
	else:
		return "User email not available or not verified by Google.", 400

	print(unique_id, users_email, users_name)

	session["email"] = users_email

	return redirect(url_for("index"))

@app.route("/logout")
def logout():
	session["email"] = None
	return redirect(url_for("index"))

if __name__ == "__main__":
	app.run(debug=True, port=5000, ssl_context="adhoc")
