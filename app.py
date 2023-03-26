from flask import Flask, redirect, request, url_for, session, render_template
from flask_session import Session

from oauthlib.oauth2 import WebApplicationClient
import requests

from pymongo import MongoClient
# import asyncio

from dotenv import load_dotenv
from gremlin_python.driver import client, serializer


from pprint import pprint

from src.traversals import dfs_until_drug, traverse_from_condition_until_drug

import os
import json
import sys

load_dotenv()




# # Quantum
# from azure.quantum import Workspace

# workspace = Workspace (
#     subscription_id = os.getenv("QUANTUM_SUBSCRIPTION_ID"), 
#     resource_group = os.getenv("QUANTUM_RESOURCE_GROUP"),   
#     name = os.getenv("QUANTUM_NAME"),          
#     location = os.getenv("QUANTUM_LOCATION")        
#     )


# from qiskit import QuantumCircuit, transpile, assemble
# from qiskit.visualization import plot_histogram
# from qiskit.tools.monitor import job_monitor
# from azure.quantum.qiskit import AzureQuantumProvider

# provider = AzureQuantumProvider(
#   resource_id=os.getenv("QUANTUM_RESOURCE_ID"),
#   location=os.getenv("QUANTUM_LOCATION")
# )










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





# Gremlin DB config

GREMLIN_URI = os.getenv("GREMLIN_URI")
GREMLIN_USER = os.getenv("GREMLIN_USER")
GREMLIN_PASSWORD = os.getenv("GREMLIN_PASSWORD")

# if sys.platform == "win32":
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

local_client = client.Client(GREMLIN_URI, "g", username=GREMLIN_USER, password=GREMLIN_PASSWORD, message_serializer=serializer.GraphSONSerializersV2d0())


# dfs_until_drug(local_client, "Malignant neoplasm of lung")




# config quantum circuit





@app.route("/")
def index():
	if not session.get("uuid"):
		return render_template("index.html")
	else:
		return session["uuid"]

@app.route("/views/search")
def views_search():
	return render_template("search.html")


@app.route("/views/results", methods=["GET", "POST"])
def views_results():
	if request.method == "POST":
		print(request.form)
		results = traverse_from_condition_until_drug(local_client, request.form["condition"])
		pprint(results)


		viewed_drugs = []

		processed_results = {"data":[]}
		for item in results:

			if item["id"] not in viewed_drugs:

				temp_dict = {
					"drugName": item["id"],
					"publicationsUri": f"https://pubmed.ncbi.nlm.nih.gov/?term={item['id']}"
					}
				processed_results["data"].append(temp_dict)


				viewed_drugs.append(item["id"])


		pprint(processed_results)
		
		return render_template("results.html", results=processed_results)
	else:
		return "User did not submit a valid POST request", 500


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

	session["uuid"] = unique_id

	return redirect(url_for("index"))

@app.route("/logout")
def logout():
	session["uuid"] = None
	return redirect(url_for("index"))

if __name__ == "__main__":
	app.run(debug=True, port=5000, ssl_context="adhoc")
