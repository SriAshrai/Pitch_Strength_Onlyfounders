document.addEventListener('DOMContentLoaded', () => {
    const pitchFile = document.getElementById('pitchFile');
    const pitchText = document.getElementById('pitchText');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const clearBtn = document.getElementById('clearBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const buttonText = document.getElementById('buttonText');
    const resultsSection = document.getElementById('resultsSection');
    const messageBox = document.getElementById('messageBox');

    const overallScore = document.getElementById('overallScore');
    const clarityScore = document.getElementById('clarityScore');
    const clarityReasoning = document.getElementById('clarityReasoning');
    const originalityScore = document.getElementById('originalityScore');
    const originalityReasoning = document.getElementById('originalityReasoning');
    const teamStrengthScore = document.getElementById('teamStrengthScore');
    const teamStrengthReasoning = document.getElementById('teamStrengthReasoning');
    const marketFitScore = document.getElementById('marketFitScore');
    const marketFitReasoning = document.getElementById('marketFitReasoning');

    const teeProcessed = document.getElementById('teeProcessed');
    const zkpHash = document.getElementById('zkpHash');
    const onChainTx = document.getElementById('onChainTx');
    const status = document.getElementById('status');

    let pitchIdCounter = 0; // Simple counter for unique pitch IDs

    // Function to display messages in the UI
    function showMessage(message, type = 'info') {
        messageBox.textContent = message;
        messageBox.className = `p-4 rounded-lg text-lg mb-4 block ${type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
        messageBox.classList.remove('hidden');
    }

    // Function to hide messages
    function hideMessage() {
        messageBox.classList.add('hidden');
    }

    // Function to set loading state
    function setLoading(isLoading) {
        if (isLoading) {
            buttonText.textContent = 'Analyzing...';
            loadingSpinner.classList.remove('hidden');
            analyzeBtn.disabled = true;
            clearBtn.disabled = true;
            hideMessage();
            resultsSection.classList.add('hidden');
        } else {
            buttonText.textContent = 'Analyze Pitch';
            loadingSpinner.classList.add('hidden');
            analyzeBtn.disabled = false;
            clearBtn.disabled = false;
        }
    }

    analyzeBtn.addEventListener('click', async () => {
        setLoading(true);
        let pitchContent = pitchText.value.trim();
        let file = pitchFile.files[0];
        let inputType = '';
        let fileText = '';

        if (file) {
            inputType = 'file';
            // For now, we'll read file content directly in JS for simplicity in the UI.
            // In a real decentralized setup, this would be encrypted and uploaded to IPFS.
            // The Python agent would then fetch from IPFS (conceptually).
            try {
                fileText = await readFileAsync(file);
                if (fileText.length > 20000) { // Simple size check to prevent huge files
                    showMessage("File is too large. Please upload files under 20KB for this demo.", "error");
                    setLoading(false);
                    return;
                }
                pitchContent = fileText; // Use file content for agent input
            } catch (error) {
                showMessage(`Error reading file: ${error.message}`, "error");
                setLoading(false);
                return;
            }
        } else if (pitchContent) {
            inputType = 'text';
            if (pitchContent.length > 10000) { // Simple size check for text
                showMessage("Pitch text is too long. Please keep it under 10KB for this demo.", "error");
                setLoading(false);
                return;
            }
        } else {
            showMessage("Please upload a pitch file or paste pitch text.", "error");
            setLoading(false);
            return;
        }

        pitchIdCounter++;
        const currentPitchId = `pitch_${String(pitchIdCounter).padStart(3, '0')}`;

        // Construct payload for the Python agent.
        // In a real scenario, this would call a backend service that wraps the Python agent.
        // For this demo, we'll simulate the call by directly calling the agent's run function (conceptual).
        const payload = {
            pitch_id: currentPitchId,
            pitch_content: inputType === 'text' ? pitchContent : null,
            file_path: inputType === 'file' ? file.name : null // We'll just pass file name, NLPProcessor will use it
        };

        try {
            // This fetch call simulates sending data to a backend server
            // that would then execute the Python LangGraph agent.
            // Replace with your actual backend endpoint if deployed.
            // For now, it will return mock data or trigger a conceptual Python execution.
            console.log("Sending payload to agent (simulated):", payload);

            // Fetch call to the local Python script, assuming it's exposed via an API.
            // IMPORTANT: In a real environment, you'd have a small backend service (e.g., Flask/FastAPI)
            // that receives this POST request and then calls the `run_pitch_strength_agent` function.
            // For this *browser-only* demo, we'll simulate the response directly.
            // You cannot directly run Python from client-side JS like this.

            // --- SIMULATED AGENT RESPONSE ---
            // In a real scenario, the result would come from an actual API call to your backend.
            // This is a placeholder for the actual fetch call.
            const simulatedResponse = await simulateAgentRun(payload);
            // --- END SIMULATION ---

            if (simulatedResponse.status === 'failed') {
                showMessage(`Analysis Failed: ${simulatedResponse.error}`, "error");
                resultsSection.classList.add('hidden');
            } else {
                displayResults(simulatedResponse);
                showMessage("Pitch analysis completed successfully!", "success");
                resultsSection.classList.remove('hidden');
            }

        } catch (error) {
            console.error("Error during pitch analysis:", error);
            showMessage(`An unexpected error occurred: ${error.message}`, "error");
            resultsSection.classList.add('hidden');
        } finally {
            setLoading(false);
        }
    });

    clearBtn.addEventListener('click', () => {
        pitchFile.value = '';
        pitchText.value = '';
        resultsSection.classList.add('hidden');
        hideMessage();
        setLoading(false);
    });

    function readFileAsync(file) {
        return new Promise((resolve, reject) => {
            let reader = new FileReader();
            reader.onload = () => {
                resolve(reader.result);
            };
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }

    function displayResults(results) {
        overallScore.textContent = results.overall_score || 'N/A';
        clarityScore.textContent = results.component_scores.clarity || 'N/A';
        clarityReasoning.textContent = results.analysis_results.components.clarity?.reasoning || '';
        originalityScore.textContent = results.component_scores.originality || 'N/A';
        originalityReasoning.textContent = results.analysis_results.components.originality?.reasoning || '';
        teamStrengthScore.textContent = results.component_scores.team_strength || 'N/A';
        teamStrengthReasoning.textContent = results.analysis_results.components.team_strength?.reasoning || '';
        marketFitScore.textContent = results.component_scores.market_fit || 'N/A';
        marketFitReasoning.textContent = results.analysis_results.components.market_fit?.reasoning || '';

        teeProcessed.textContent = results.privacy_flags.tee_processed ? 'Yes' : 'No';
        zkpHash.textContent = results.privacy_flags.zkp_hash || 'N/A';
        onChainTx.textContent = results.on_chain_tx_hash || 'N/A';
        status.textContent = results.status || 'N/A';
    }

    // --- SIMULATED AGENT RUN (FOR BROWSER-ONLY DEMO) ---
    // In a real setup, this would be a fetch call to a backend API endpoint.
    // We cannot directly import and run Python functions in a browser JS environment.
    async function simulateAgentRun(payload) {
        console.warn("--- Simulating Agent Run ---");
        console.warn("This is a mock for browser-only demonstration. In a real app, this would be an API call to a backend running the Python agent.");

        // Mock a direct call to the Python agent's analysis logic
        // This *cannot* run directly in the browser; it's illustrative.
        // In a real environment, you'd have a small backend service (e.g., Flask/FastAPI)
        // that receives this POST request and then calls the `run_pitch_strength_agent` function.

        // Placeholder for the mock data structure matching the Python agent's output
        const mockResults = {
            "pitch_id": payload.pitch_id,
            "overall_score": Math.floor(Math.random() * 10) + 1, // Random score 1-10
            "component_scores": {
                "clarity": Math.floor(Math.random() * 10) + 1,
                "originality": Math.floor(Math.random() * 10) + 1,
                "team_strength": Math.floor(Math.random() * 10) + 1,
                "market_fit": Math.floor(Math.random() * 10) + 1
            },
            "analysis_results": { // Mimic the structure for reasoning
                "components": {
                    "clarity": {"score": null, "reasoning": "Mock: Clarity is based on a structured approach."},
                    "originality": {"score": null, "reasoning": "Mock: Originality is high due to unique market perspective."},
                    "team_strength": {"score": null, "reasoning": "Mock: Team has diverse experience."},
                    "market_fit": {"score": null, "reasoning": "Mock: Strong problem-solution alignment."}
                }
            },
            "privacy_flags": {
                "tee_processed": true,
                "zkp_hash": "0x" + Array.from({length: 32}, () => Math.floor(Math.random() * 256).toString(16).padStart(2, '0')).join('')
            },
            "status": "completed",
            "on_chain_tx_hash": "0x" + Array.from({length: 32}, () => Math.floor(Math.random() * 256).toString(16).padStart(2, '0')).join('')
        };

        await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate network latency

        return mockResults;
    }
});

