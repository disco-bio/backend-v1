import os
from dotenv import load_dotenv

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

from pprint import pprint

provider = AzureQuantumProvider(
	resource_id=os.getenv("QUANTUM_RESOURCE_ID"),
	location=os.getenv("QUANTUM_LOCATION")
	)

print(workspace)
print(provider)


def compute_quantum(provider, not_gate_1=False, not_gate_2=False):


	q_register = QuantumRegister(2, "q")
	c_register = ClassicalRegister(2, "c")

	circuit = QuantumCircuit(q_register, c_register)

	circuit.reset(q_register[0])
	circuit.reset(q_register[1])

	# circuit.x(q_register[1])
	circuit.cx(q_register[0], q_register[1])

	circuit.measure(q_register[0], c_register[0])
	circuit.measure(q_register[1], c_register[1])

	simulator_backend = provider.get_backend("ionq.simulator")


	transpiled_circuit = transpile(circuit, simulator_backend)
	qobj = assemble(transpiled_circuit)



	# Submit the circuit to run on Azure Quantum
	job = simulator_backend.run(qobj, shots=100)
	job_id = job.id()
	print("Job id", job_id)

	# Monitor job progress and wait until complete:
	job_monitor(job)

	result = job.result()
	key_ = str(list(result.get_counts().keys())[0])
	return key_


def compute_binary_probability(provider):

	q_register = QuantumRegister(1, "q")
	c_register = ClassicalRegister(1, "c")

	circuit = QuantumCircuit(q_register, c_register)

	circuit.reset(q_register[0])
	circuit.h(q_register[0])
	circuit.measure(q_register[0], c_register[0])

	simulator_backend = provider.get_backend("ionq.simulator")

	transpiled_circuit = transpile(circuit, simulator_backend)
	qobj = assemble(transpiled_circuit)


	# Submit the circuit to run on Azure Quantum
	job = simulator_backend.run(qobj, shots=100)
	job_id = job.id()
	print("Job id", job_id)

	# Monitor job progress and wait until complete:
	job_monitor(job)

	result = job.result()

	# circuit.measure(q_register[0], c_register[0])
	# simulator_backend = provider.get_backend("ionq.simulator")


	return result.get_counts()

	# key_ = str(list(result.get_counts().keys())[0])
	# return key_

pprint(compute_quantum(provider, not_gate_1=True, not_gate_2=False))
pprint(compute_binary_probability(provider))