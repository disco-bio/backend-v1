import requests
import json


def return_drug_summary(
	drug_name, 
	OPENAI_KEY, 
	model_name="text-davinci-003",
	temperature=0.1,
	max_tokens=100,
	URL="https://api.openai.com/v1/completions"
	):


	HEADERS = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {OPENAI_KEY}"
	}

	BODY = {
		"model": model_name,
		"prompt": f"Summarize {drug_name} in less than 30 words.",
		"temperature": temperature,
		"max_tokens": max_tokens
	}

	resp = requests.post(
		URL,
		headers=HEADERS,
		data=json.dumps(BODY)
		)

	cleaned_text = resp.json()["choices"][0]["text"].replace("\n", "")
	return cleaned_text