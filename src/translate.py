import requests, uuid, json
import os
import dotenv

dotenv.load_dotenv()

key = os.getenv("TRANSLATOR_KEY")
endpoint = os.getenv("TRANSLATOR_ENDPOINT")
location = os.getenv("TRANSLATOR_LOCATION")
path = "/translate"

TRANSLATE_URL = endpoint + path

parameter_dict = {
	"api-version": "3.0",
	"from": "en",
	"to": None
}

headers = {
    'Ocp-Apim-Subscription-Key': key,
    # location required if you're using a multi-service or regional (not global) resource.
    'Ocp-Apim-Subscription-Region': location,
    'Content-type': 'application/json',
    'X-ClientTraceId': str(uuid.uuid4())
}

def translate(text, language_to, parameter_dict=parameter_dict, headers=headers):
	body = [{"text": text}]
	parameter_dict["to"] = language_to
	resp = requests.post(TRANSLATE_URL, params=parameter_dict, headers=headers, json=body)
	resp_json = resp.json()

	return resp_json
