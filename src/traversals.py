from pprint import pprint

def dfs_until_drug(gremlin_client, condition_name):
	stack = [condition_name]
	_COMMAND = f"g.V().hasLabel('condition').has('id', '{condition_name}').outE('links')"
	callback = gremlin_client.submitAsync(_COMMAND)
	visited = [condition_name]

	counter = 0

	while counter < 100 and len(stack) != 0:

		print(counter)

		for item in callback.result().all().result():
			if item["inVLabel"] == "drug":
				print("found!")
				pprint(item)
				return item
			else:
				stack.append(item["inV"])

		gene_name = stack.pop()
		if gene_name not in visited:

			visited.append(gene_name)
			_COMMAND = f"g.V().hasLabel('gene').has('id', '{gene_name}').outE('links')"
			counter += 1
			callback = gremlin_client.submitAsync(_COMMAND)


	# pprint(callback.result().all().result())
	return True

def traverse_from_condition_until_drug(local_client, condition_name=None):
    _COMMAND = f"g.V().hasLabel('condition').has('id', '{condition_name}').repeat(out()).until(hasLabel('drug')).limit(20)"
    callback = local_client.submitAsync(_COMMAND)
    results = callback.result().all().result()
    return results
