from qiskit import QuantumCircuit, Aer, execute
from qiskit.qasm import QasmError
from typing import Dict, Any

class QuantumService:
    def __init__(self):
        # Use Qiskit's qasm_simulator backend for circuit execution
        self.simulator = Aer.get_backend('qasm_simulator')

    async def analyze_qasm(self, qasm_code: str) -> Dict[str, Any]:
        """
        Analyze the QASM code and return metadata about the circuit.
        """
        try:
            circuit = QuantumCircuit.from_qasm_str(qasm_code)
            return {
                "qubit_count": circuit.num_qubits,
                "clbit_count": circuit.num_clbits,
                "ancilla_count": getattr(circuit, "num_ancillas", 0),  # Qiskit 0.45+ supports ancillas[1]
                "gate_count": len(circuit.data),
                "depth": circuit.depth(),
                "valid": True
            }
        except QasmError as e:
            raise ValueError(f"Invalid QASM code: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error analyzing QASM: {str(e)}")

    async def execute_circuit(self, qasm_code: str, shots: int = 1024) -> Dict[str, Any]:
        """
        Execute the quantum circuit on the simulator and return the measurement results.
        """
        try:
            circuit = QuantumCircuit.from_qasm_str(qasm_code)
            # Ensure the circuit has measurements; if not, add measurements to all qubits
            if not any(instr.operation.name == 'measure' for instr in circuit.data):
                circuit.measure_all()
            job = execute(circuit, self.simulator, shots=shots)
            result = job.result()
            counts = result.get_counts(circuit)
            probabilities = {k: v / shots for k, v in counts.items()}
            return {
                "counts": counts,
                "shots": shots,
                "success": True,
                "probabilities": probabilities
            }
        except QasmError as e:
            return {"error": f"Invalid QASM code: {str(e)}", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

# Singleton instance for import
quantum_service = QuantumService()
