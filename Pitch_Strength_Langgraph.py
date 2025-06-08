import asyncio
import json
import os
from typing import Dict, Any, List, Literal

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END

# Import our custom NLPProcessor
# Ensure nlp_processor.py is in the same directory or accessible via PYTHONPATH
from nlp_processor import NLPProcessor

# --- 1. Define Agent State ---
class AgentState(BaseModel):
    """
    Represents the state of the Pitch Strength Agent's workflow.
    """
    pitch_id: str = Field(description="Unique identifier for the pitch being analyzed.")
    pitch_content: str = Field(None, description="Raw text content of the pitch.")
    file_path: str = Field(None, description="Path to the pitch file (PDF, DOCX, TXT).")
    analysis_results: Dict[str, Any] = Field(None, description="Detailed pitch analysis scores.")
    zkp_hash: str = Field(None, description="Hash of the generated ZKP for the scores.")
    tee_processed: bool = Field(False, description="Flag indicating if pitch was processed securely in a TEE.")
    error: str = Field(None, description="Any error message encountered during processing.")
    # Add a field for the raw, encrypted pitch content for TEE/Decentralized Storage
    encrypted_pitch_cid: str = Field(None, description="CID of the encrypted pitch on decentralized storage (e.g., IPFS).")


# --- 2. Initialize Tools / Services ---
# Instantiate the NLPProcessor. In a real deployment, this might be a service call
# to an NLP service running within a TEE or a ZKP-friendly computation environment.
nlp_processor_instance = NLPProcessor() # This instance will conceptually run in a TEE or be ZKP-compatible

# Mock Ethereum interaction (replace with web3.py in real app)
class MockWeb3:
    def __init__(self, contract_address: str):
        self.contract_address = contract_address
        print(f"MockWeb3: Initialized for contract at {contract_address}")

    async def record_pitch_score(self, pitch_id: bytes, overall_score: int, clarity_score: int,
                                 originality_score: int, team_strength_score: int,
                                 market_fit_score: int, zkp_hash: bytes):
        """Mocks sending a transaction to the PitchRegistry smart contract."""
        print(f"\n[MockWeb3] Simulating on-chain recording for pitch {pitch_id.hex()}...")
        print(f"  Overall Score: {overall_score}")
        print(f"  ZKP Hash: {zkp_hash.hex()}")
        # In a real scenario, this would involve web3.py, transaction signing, and sending
        await asyncio.sleep(1) # Simulate transaction time
        print(f"[MockWeb3] Pitch score recorded on-chain (mock).")
        return {"transaction_hash": f"0x{os.urandom(32).hex()}"} # Mock Tx hash

# Instantiate the mock Web3 client (replace with actual web3.py client)
MOCK_CONTRACT_ADDRESS = "0xPitchRegistryContractAddress" # Placeholder address
web3_client = MockWeb3(MOCK_CONTRACT_ADDRESS)

# --- 3. Define Agent Nodes (Functions) ---

async def load_and_preprocess_pitch(state: AgentState) -> AgentState:
    """
    Loads pitch content from file or uses provided string.
    In a real scenario, this would involve:
    1. Client-side encryption of the pitch.
    2. Uploading the encrypted pitch to IPFS/Arweave to get a CID.
    3. The agent receiving the encrypted_pitch_cid (instead of raw content/file_path).
    For this mock, we'll continue using file_path/pitch_content for demonstration,
    but conceptualize the encryption/upload happening before this node.
    """
    print(f"\n[Pitch Strength Agent] Loading pitch for ID: {state.pitch_id}")
    if state.file_path:
        # Conceptual: This is where client-side encryption and IPFS upload would happen.
        # For demo, NLPProcessor will still read from file.
        print(f"[Pitch Strength Agent] Using file path: {state.file_path}")
        # Assuming encrypted_pitch_cid is obtained here from decentralized storage
        return {"encrypted_pitch_cid": f"ipfs://{state.pitch_id}_encrypted_pitch.bin"}
    elif state.pitch_content:
        # Conceptual: This is where client-side encryption and IPFS upload would happen.
        # For demo, NLPProcessor will use string content.
        print("[Pitch Strength Agent] Using provided pitch content string.")
        return {"encrypted_pitch_cid": f"ipfs://{state.pitch_id}_encrypted_pitch_string.bin"}
    else:
        return {"error": "No pitch content or file path provided to the agent."}

async def process_with_tee(state: AgentState) -> AgentState:
    """
    Simulates processing the *encrypted* pitch content within a Trusted Execution Environment (TEE).
    This is where the actual decryption and NLP analysis would happen in a secure enclave.
    """
    print(f"\n[Pitch Strength Agent] Initiating TEE processing for pitch ID: {state.pitch_id} (CID: {state.encrypted_pitch_cid})...")
    if state.error:
        print("[Pitch Strength Agent] Skipping TEE due to prior error.")
        return {} # Pass through if there's an error
    try:
        # --- CONCEPTUAL TEE LOGIC ---
        # 1. The agent securely requests the encrypted pitch data associated with state.encrypted_pitch_cid
        #    from decentralized storage.
        # 2. This data is streamed into the TEE.
        # 3. Inside the TEE, the pitch is *decrypted* using a key that was securely provided
        #    to the TEE (e.g., via attestation from the user, or a shared secret with the protocol).
        # 4. The NLPProcessor.analyze_pitch() is called *within the TEE* on the decrypted text.
        #    For this mock, we'll call it here as if it's running in the TEE.
        print(f"[Pitch Strength Agent] TEE: Decrypting and analyzing pitch content...")
        results = await nlp_processor_instance.analyze_pitch(
            pitch_id=state.pitch_id,
            pitch_content=state.pitch_content, # In real TEE, this would be decrypted from CID
            file_path=state.file_path # In real TEE, this would be decrypted from CID
        )

        if "error" in results:
            print(f"[Pitch Strength Agent] TEE analysis failed: {results['error']}")
            return {"error": f"TEE analysis failed: {results['error']}"}

        # 5. The TEE would then output the analysis results, potentially re-encrypted,
        #    or serve as the environment for ZKP generation directly on the results.
        print(f"[Pitch Strength Agent] Pitch {state.pitch_id} processed within TEE.")
        return {
            "tee_processed": True,
            "analysis_results": results # Results are now conceptually 'secured' by TEE context
        }
    except Exception as e:
        return {"error": f"TEE processing or internal NLP error: {e}"}

async def generate_zkp_for_scores(state: AgentState) -> AgentState:
    """
    Generates a Zero-Knowledge Proof for the calculated pitch scores.
    This step would ideally happen within or after the TEE processing to maintain privacy.
    """
    print(f"\n[Pitch Strength Agent] Initiating ZKP generation for pitch ID: {state.pitch_id}...")
    if state.error or not state.analysis_results:
        print("[Pitch Strength Agent] Skipping ZKP due to prior error or missing analysis results.")
        return {} # Pass through if there's an error or no analysis

    try:
        # --- CONCEPTUAL ZKP LOGIC ---
        # Public Inputs: overall_score, component_scores (or their hashes/ranges)
        # Private Witness: The raw pitch content, intermediate NLP computations, specific scoring weights.
        # 1. Select a ZKP library (e.g., Circom + SnarkJS, Gnark).
        # 2. Define the ZKP circuit: This circuit takes the original pitch content (or derived features)
        #    as a private "witness" and the final scores as "public inputs". The circuit proves
        #    that the public scores were correctly derived from the private pitch according to
        #    the pitch scoring algorithm.
        # 3. Generate the proof: Call the ZKP prover (this is computationally intensive!).
        #    E.g., `proof = await run_circom_prover(pitch_data, scoring_logic)`
        # 4. Compute the public hash of the proof (or public inputs).
        #    This is what will be stored on-chain.
        
        # MOCK ZKP Generation (replace with actual ZKP library calls)
        mock_proof_data = {
            "overall": state.analysis_results.get("overall_score"),
            "clarity": state.analysis_results.get("components", {}).get("clarity", {}).get("score"),
            "originality": state.analysis_results.get("components", {}).get("originality", {}).get("score")
        }
        # A hash of the public inputs for the ZKP
        zkp_public_inputs_hash = hashlib.sha256(json.dumps(mock_proof_data, sort_keys=True).encode()).hexdigest()
        
        await asyncio.sleep(0.5) # Simulate ZKP generation time
        print(f"[Pitch Strength Agent] ZKP mock generated for pitch {state.pitch_id}. Hash: {zkp_public_inputs_hash}")
        return {"zkp_hash": "0x" + zkp_public_inputs_hash} # Store as hex string for on-chain compatibility
    except Exception as e:
        return {"error": f"ZKP generation simulation failed: {e}"}

async def record_on_chain(state: AgentState) -> AgentState:
    """
    Records the finalized pitch scores and ZKP hash on the blockchain.
    """
    print(f"\n[Pitch Strength Agent] Recording pitch scores on-chain for ID: {state.pitch_id}...")
    if state.error or not state.analysis_results or not state.zkp_hash:
        print("[Pitch Strength Agent] Skipping on-chain record due to prior error or missing data.")
        return {"error": state.error or "Missing analysis results or ZKP hash for on-chain record."}

    try:
        overall_score = state.analysis_results.get("overall_score", 0)
        component_scores = state.analysis_results.get("components", {})
        clarity_score = component_scores.get("clarity", {}).get("score", 0)
        originality_score = component_scores.get("originality", {}).get("score", 0)
        team_strength_score = component_scores.get("team_strength", {}).get("score", 0)
        market_fit_score = component_scores.get("market_fit", {}).get("score", 0)

        # Convert pitch_id to bytes32 for Solidity
        pitch_id_bytes = bytes.fromhex(state.pitch_id.replace("pitch_", "").ljust(64, '0')[:64]) # Simple mock conversion
        # Convert zkp_hash to bytes32 for Solidity (remove 0x prefix and pad if needed)
        zkp_hash_bytes = bytes.fromhex(state.zkp_hash[2:]) if state.zkp_hash else b'\x00' * 32

        tx_receipt = await web3_client.record_pitch_score(
            pitch_id_bytes,
            overall_score,
            clarity_score,
            originality_score,
            team_strength_score,
            market_fit_score,
            zkp_hash_bytes
        )
        print(f"[Pitch Strength Agent] On-chain record successful! Tx Hash: {tx_receipt['transaction_hash']}")
        return {"status": "completed", "on_chain_tx_hash": tx_receipt['transaction_hash']}
    except Exception as e:
        return {"error": f"Failed to record on-chain: {e}"}

# This function is now just an intermediate step for final output formatting,
# the actual on-chain recording is done in `record_on_chain`.
async def final_output_format(state: AgentState) -> Dict[str, Any]:
    """
    Prepares the final output for the agent, after on-chain recording.
    """
    print(f"\n[Pitch Strength Agent] Finalizing agent output for pitch ID: {state.pitch_id}...")
    if state.error:
        return {"status": "failed", "pitch_id": state.pitch_id, "error": state.error}
    else:
        final_data = {
            "pitch_id": state.pitch_id,
            "overall_score": state.analysis_results.get("overall_score"),
            "component_scores": {k: v['score'] for k, v in state.analysis_results.get("components", {}).items()},
            "privacy_flags": {
                "tee_processed": state.tee_processed,
                "zkp_hash": state.zkp_hash
            },
            "status": "completed",
            "on_chain_tx_hash": state.get("on_chain_tx_hash") # Get tx hash from previous node
        }
        print(f"[Pitch Strength Agent] Agent workflow finished for pitch {state.pitch_id}.")
        return final_data

# --- 4. Build the LangGraph Workflow ---

workflow = StateGraph(AgentState)

# Add nodes to the graph
workflow.add_node("load_pitch", load_and_preprocess_pitch)
workflow.add_node("process_tee", process_with_tee)
workflow.add_node("generate_zkp", generate_zkp_for_scores)
workflow.add_node("record_on_chain", record_on_chain) # New node for on-chain interaction
workflow.add_node("output_results", final_output_format) # Renamed to avoid confusion with the final output of the agent

# Define the entry point
workflow.set_entry_point("load_pitch")

# Define edges (transitions between nodes)
workflow.add_edge("load_pitch", "process_tee")
workflow.add_edge("process_tee", "generate_zkp") # ZKP happens after TEE processing is conceptualized
workflow.add_edge("generate_zkp", "record_on_chain") # Record on-chain after ZKP is generated
workflow.add_edge("record_on_chain", "output_results") # Final output formatting
workflow.add_edge("output_results", END)

# Compile the graph
app = workflow.compile()

# --- 5. Example Usage (Running the Agent) ---
async def run_pitch_strength_agent(pitch_id: str, pitch_content: str = None, file_path: str = None):
    """
    Function to run the Pitch Strength Agent workflow.
    """
    initial_state = AgentState(
        pitch_id=pitch_id,
        pitch_content=pitch_content,
        file_path=file_path
    )
    print(f"\n--- Starting Pitch Strength Agent for Pitch ID: {pitch_id} ---")
    final_state = None
    # We explicitly iterate through the stream to observe state changes
    async for step in app.stream(initial_state, {"recursion_limit": 100}):
        # 'step' is a dictionary where keys are node names and values are their outputs
        for node_name, output in step.items():
            print(f"Node '{node_name}' executed. Output keys: {list(output.keys())}")
            # Update the 'state' variable to reflect the latest state after each step
            # This is a common pattern when you want to inspect intermediate states
            if isinstance(output, dict):
                # Ensure we are working with the correct state update from the node
                initial_state = initial_state.copy(update=output)
            else:
                print(f"Warning: Node '{node_name}' did not return a dict. Output: {output}")
        # After each step, the overall graph state is passed to the next node
        # The 'END' node's output will be the final result we care about for the entire graph
        if END in step:
            final_state = step[END]
            break # Exit loop once END is reached

    print(f"--- Finished Pitch Strength Agent for Pitch ID: {pitch_id} ---")
    # Return the final output from the 'output_results' node, which is the last before END
    return final_state

if __name__ == "__main__":
    # Ensure nlp_processor.py exists in the same directory for this to run locally.
    # Create a dummy pitch file for demonstration
    dummy_pitch_content_demo = """
    Introducing 'EcoConnect', a blockchain-powered platform for tracking sustainable supply chains.
    Our team comprises seasoned developers with expertise in IoT and Solidity, and environmental scientists from leading universities.
    We address the critical lack of transparency in global supply chains, enabling consumers to verify product origins and environmental impact.
    The market for sustainable products is booming, with increasing consumer demand for ethical sourcing. We aim to capture a significant share by providing verifiable data.
    """
    dummy_file_path = "demo_pitch.txt"
    with open(dummy_file_path, "w") as f:
        f.write(dummy_pitch_content_demo)

    # Required for ZKP hash generation mock
    import hashlib

    print("\n--- Running Agent with File Input ---")
    result_file = asyncio.run(run_pitch_strength_agent("pitch_file_001", file_path=dummy_file_path))
    print("\nFinal Result from Agent (File Input):")
    print(json.dumps(result_file, indent=2))

    # Run the agent with direct content string
    print("\n--- Running Agent with String Content Input ---")
    result_content = asyncio.run(run_pitch_strength_agent("pitch_string_002", pitch_content=dummy_pitch_content_demo))
    print("\nFinal Result from Agent (String Content Input):")
    print(json.dumps(result_content, indent=2))

    # Clean up dummy file
    os.remove(dummy_file_path)
