def create_user(mongo_client, uuid, email, name, photoUri):
	user_object = {
		"uuid": uuid,
		"email": email,
		"name": name,
		"photoUri": photoUri,
		"savedMedication": []
	}

	discoV1Prod = mongo_client.discoV1Prod
	users = discoV1Prod.users

	users.insert_one(user_object)

	return True