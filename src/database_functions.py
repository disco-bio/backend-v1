def create_user(mongo_client, uuid, email, name, photoUri):
	user_object = {
		"uuid": uuid,
		"email": email,
		"name": name,
		"photoUri": photoUri,
		"savedMedication": []
	}

	discoV1Test = mongo_client.discoV1Test
	users = discoV1Test.users

	users.insert_one(user_object)

	return True