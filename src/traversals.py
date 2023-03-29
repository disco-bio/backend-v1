from pprint import pprint
import random

import os
from dotenv import load_dotenv

from threading import Thread
from gremlin_python.driver import client, serializer

import time

load_dotenv()

from azure.quantum import Workspace

workspace = Workspace(
	subscription_id=os.getenv("QUANTUM_SUBSCRIPTION_ID"),
	resource_group=os.getenv("QUANTUM_RESOURCE_GROUP"),
	name=os.getenv("QUANTUM_NAME"),
	location=os.getenv("QUANTUM_LOCATION")
	)

from qiskit import QuantumCircuit, transpile, assemble
from qiskit import QuantumRegister, ClassicalRegister
# from qiskit.visualization import plot_histogram
from qiskit.tools.monitor import job_monitor
from azure.quantum.qiskit import AzureQuantumProvider

provider = AzureQuantumProvider(
	resource_id=os.getenv("QUANTUM_RESOURCE_ID"),
	location=os.getenv("QUANTUM_LOCATION")
	)



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

	return True



class QuantumStoppingTracker():

	def __init__(self, provider):
		self.result_key = "00"
		self.provider=provider
		self.results = []


	def add_result(self, result):
		self.results.append(result)

	def is_stopped(self):
		# print(self.result_key)
		if self.result_key != "00":
			return True
		else:
			return False

	def compute_quantum(self, not_gate_1=False, not_gate_2=False):

		print("computing quantum...")


		q_register = QuantumRegister(2, "q")
		c_register = ClassicalRegister(2, "c")

		circuit = QuantumCircuit(q_register, c_register)

		circuit.reset(q_register[0])
		circuit.reset(q_register[1])

		# circuit.x(q_register[1])

		if not_gate_1:
			circuit.x(q_register[0])

		if not_gate_2:
			circuit.x(q_register[1])

		circuit.cx(q_register[0], q_register[1])

		circuit.measure(q_register[0], c_register[0])
		circuit.measure(q_register[1], c_register[1])

		simulator_backend = self.provider.get_backend("ionq.simulator")


		transpiled_circuit = transpile(circuit, simulator_backend)
		qobj = assemble(transpiled_circuit)

		print("submitting job...")


		# Submit the circuit to run on Azure Quantum
		job = simulator_backend.run(qobj, shots=100)
		job_id = job.id()
		print("Job id", job_id)

		# Monitor job progress and wait until complete:
		job_monitor(job)

		result = job.result()
		key_ = str(list(result.get_counts().keys())[0])

		self.result_key = key_

		return key_




def dfs_until_drug_with_quantum(gremlin_client, condition_name, quantum_obj, quantum_index_dict):


	def skip_node():
		random_number_binary = random.choice([0,1])
		if random_number_binary==0:
			return False
		else:
			return True


	stack = [condition_name]
	_COMMAND = f"g.V().hasLabel('condition').has('id', '{condition_name}').outE('links')"
	callback = gremlin_client.submitAsync(_COMMAND)
	visited = [condition_name]

	counter = 0

	while counter < 100 and len(stack) != 0 and (not quantum_obj.is_stopped()):

		print(counter)

		for item in callback.result().all().result():

			# if True:
			if not skip_node():

				if item["inVLabel"] == "drug":
					print("found!")
					pprint(item)

					quantum_obj.compute_quantum(not_gate_1=quantum_index_dict["0"], not_gate_2=quantum_index_dict["1"])				
					quantum_obj.add_result(item)
					print("item is added")
					return item
				else:

					stack.append(item["inV"])

		gene_name = stack.pop()
		if gene_name not in visited:

			visited.append(gene_name)
			_COMMAND = f"g.V().hasLabel('gene').has('id', '{gene_name}').outE('links')"
			counter += 1
			callback = gremlin_client.submitAsync(_COMMAND)

	return None





def traverse_from_condition_until_drug(local_client, condition_name=None):
    _COMMAND = f"g.V().hasLabel('condition').has('id', '{condition_name}').repeat(out()).until(hasLabel('drug')).limit(20)"
    callback = local_client.submitAsync(_COMMAND)
    results = callback.result().all().result()
    return results









def quantum_traversal_2_qubit_wrapper(gremlin_client, quantum_provider, condition_name):

	q_obj = QuantumStoppingTracker(quantum_provider)

	thread_1 = Thread(target=dfs_until_drug_with_quantum, args=(gremlin_client, condition_name, q_obj, {"0": True, "1": False}))
	thread_2 = Thread(target=dfs_until_drug_with_quantum, args=(gremlin_client, condition_name, q_obj, {"0": False, "1": True}))

	thread_1.start()
	thread_2.start()

	thread_1.join()
	thread_2.join()

	return q_obj.results







if __name__ == "__main__":

	# Gremlin DB config

	GREMLIN_URI = os.getenv("GREMLIN_URI")
	GREMLIN_USER = os.getenv("GREMLIN_USER")
	GREMLIN_PASSWORD = os.getenv("GREMLIN_PASSWORD")

	# if sys.platform == "win32":
	    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

	gremlin_client = client.Client(GREMLIN_URI, "g", username=GREMLIN_USER, password=GREMLIN_PASSWORD, message_serializer=serializer.GraphSONSerializersV2d0())


	q_obj = QuantumStoppingTracker(provider)

	# main program part

	thread_1 = Thread(target=dfs_until_drug_with_quantum, args=(gremlin_client, "Malaria", q_obj, {"0":True, "1":False}))
	# thread_2 = Thread(target=dfs_until_drug_with_quantum, args=(gremlin_client, "Malaria", q_obj, {"0":False, "1":True}))

	thread_1.start()
	# thread_2.start()

	thread_1.join()
	# thread_2.join()

	print(q_obj.results)



	q_obj = QuantumStoppingTracker(provider)

	thread_1 = Thread(target=dfs_until_drug_with_quantum, args=(gremlin_client, "Malaria", q_obj, {"0":True, "1":False}))
	thread_2 = Thread(target=dfs_until_drug_with_quantum, args=(gremlin_client, "Malaria", q_obj, {"0":False, "1":True}))

	thread_1.start()
	thread_2.start()

	thread_1.join()
	thread_2.join()

	print(q_obj.results)