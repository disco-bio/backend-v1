from flask import Flask, redirect, request, url_for, session, render_template
from flask_session import Session

from oauthlib.oauth2 import WebApplicationClient
import requests

from pymongo import MongoClient

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


MONGODB_URI = os.getenv("MONGODB_URI")

oauth_client = WebApplicationClient(GOOGLE_CLIENT_ID)
pymongo_client = MongoClient()


def get_google_provider_cfg():
	return requests.get(GOOGLE_DISCOVERY_URL).json()

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


app.secret_key = os.urandom(24)

@app.route("/")
def index():
	if not session.get("email"):
		return render_template("index.html")
	else:
		return session["email"]

@app.route("/login")
def login():
	google_provider_cfg = get_google_provider_cfg()
	auth_endpoint = google_provider_cfg["authorization_endpoint"]

	redirect_uri_custom = request.base_url + "/callback"

	request_uri = oauth_client.prepare_request_uri(
		auth_endpoint,
		redirect_uri = redirect_uri_custom.replace("http://", "https://"),
		scope = ["openid", "email", "profile"]
		)
	return redirect(request_uri)

@app.route("/login/callback")
def callback():
	code = request.args.get("code")
	google_provider_cfg = get_google_provider_cfg()
	token_endpoint = google_provider_cfg["token_endpoint"]

	print("redirect_url", request.base_url)

	token_url, headers, body = oauth_client.prepare_token_request(
		token_endpoint,
		authorization_response=request.url.replace("http://", "https://"),
		redirect_url=request.base_url.replace("http://", "https://"),
		code=code
		)
	token_response = requests.post(
		token_url,
		headers=headers,
		data=body,
		auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
		)
	oauth_client.parse_request_body_response(json.dumps(token_response.json()))

	userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
	uri, headers, body = oauth_client.add_token(userinfo_endpoint)
	userinfo_response = requests.get(uri, headers=headers, data=body)

	print("keys:", userinfo_response.json().keys())

	if userinfo_response.json().get("email_verified"):
		unique_id = userinfo_response.json()["sub"]
		users_email = userinfo_response.json()["email"]
		users_name = userinfo_response.json()["given_name"]
		users_photo_uri = userinfo_response.json()["picture"]
	else:
		return "User email not available or not verified by Google.", 400

	print(unique_id, users_email, users_name, users_photo_uri)

	session["email"] = users_email

	return redirect(url_for("index"))

@app.route("/logout")
def logout():
	session["email"] = None
	return redirect(url_for("index"))

if __name__ == "__main__":
	app.run(debug=True, port=5000, ssl_context="adhoc")
