import os
from dotenv import load_dotenv
from typing import Dict, Any, List
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import asyncio

# For Gemini API integration
import google.generativeai as genai
from langchain_google_generativeai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Load environment variables from .env file
load_dotenv()

class NLPProcessor:
    def __init__(self):
        # Configure Gemini API
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            print("GEMINI_API_KEY not found in .env file. Please set it up.")
            # For Canvas, if API key is empty, it will be automatically provided at runtime.
            # However, for local testing, ensure it's set.
            genai.configure(api_key="") # Will be filled by Canvas runtime or you provide your key
        else:
             genai.configure(api_key=self.gemini_api_key)

        # Initialize the Sentence Transformer for originality checks
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("NLPProcessor: Loaded Sentence Transformer model for originality.")

        # Initialize LangChain's Gemini LLM for complex text analysis
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2) # Use gemini-pro for text tasks

        # Define prompts for LLM-based scoring
        self.clarity_prompt = PromptTemplate(
            template="""You are an expert pitch evaluator.
            Assess the clarity and structure of the following startup pitch.
            Score it on a scale of 1 to 10 (10 being perfectly clear and well-structured).
            Provide a brief reasoning for the score.
            Format your response as a JSON object with keys 'score' (integer) and 'reasoning' (string).

            Pitch:
            {pitch_text}
            """,
            input_variables=["pitch_text"],
        )

        self.team_strength_prompt = PromptTemplate(
            template="""You are an expert pitch evaluator focused on team assessment.
            Analyze the following pitch for explicit and implicit indicators of team strength (experience, relevant background, cohesion, previous successes).
            Score it on a scale of 1 to 10 (10 being an exceptionally strong team).
            Provide a brief reasoning for the score.
            Format your response as a JSON object with keys 'score' (integer) and 'reasoning' (string).

            Pitch:
            {pitch_text}
            """,
            input_variables=["pitch_text"],
        )

        self.market_fit_prompt = PromptTemplate(
            template="""You are an expert pitch evaluator focused on market fit.
            Evaluate the following pitch for its understanding of the market, problem-solution fit, and competitive landscape.
            Score it on a scale of 1 to 10 (10 being an outstanding market fit).
            Provide a brief reasoning for the score.
            Format your response as a JSON object with keys 'score' (integer) and 'reasoning' (string).

            Pitch:
            {pitch_text}
            """,
            input_variables=["pitch_text"],
        )

        self.json_parser = JsonOutputParser()
        print("NLPProcessor: Initialized LLM and scoring prompts.")


    async def _call_llm_for_score(self, prompt: PromptTemplate, pitch_text: str) -> Dict[str, Any]:
        """Helper to call LLM with a specific prompt and parse JSON output."""
        try:
            chain = prompt | self.llm | self.json_parser
            response = await chain.ainvoke({"pitch_text": pitch_text})
            return response
        except Exception as e:
            print(f"Error calling LLM for scoring: {e}")
            return {"score": 0, "reasoning": f"LLM error: {e}"}

    def _extract_text_from_doc(self, file_path: str) -> str:
        """Extracts text from PDF, DOCX, or TXT files."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        text = ""
        if file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif file_path.endswith('.docx'):
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError("Unsupported file format. Only PDF, DOCX, and TXT are supported.")
        return text

    async def analyze_pitch(self, pitch_id: str, pitch_content: str = None, file_path: str = None) -> Dict[str, Any]:
        """
        Analyzes a pitch for clarity, team strength, market fit, and originality.
        Takes either direct pitch_content (string) or a file_path.
        """
        if file_path:
            try:
                pitch_text = self._extract_text_from_doc(file_path)
                print(f"NLPProcessor: Extracted text from file: {file_path}")
            except Exception as e:
                print(f"NLPProcessor: Error extracting text from {file_path}: {e}")
                return {"error": str(e)}
        elif pitch_content:
            pitch_text = pitch_content
            print("NLPProcessor: Using provided pitch content string.")
        else:
            return {"error": "No pitch content or file path provided."}

        # Truncate pitch_text if too long for LLM context window,
        # or for originality check to manage memory.
        # Max tokens for gemini-pro is 32k. For simplicity, let's keep it under 10k chars.
        processed_pitch_text = pitch_text[:10000]

        scores = {
            "pitch_id": pitch_id,
            "overall_score": 0,
            "components": {}
        }

        # --- Component Scoring using LLM ---
        print("NLPProcessor: Calling LLM for clarity score...")
        clarity_result = await self._call_llm_for_score(self.clarity_prompt, processed_pitch_text)
        scores['components']['clarity'] = clarity_result

        print("NLPProcessor: Calling LLM for team strength score...")
        team_strength_result = await self._call_llm_for_score(self.team_strength_prompt, processed_pitch_text)
        scores['components']['team_strength'] = team_strength_result

        print("NLPProcessor: Calling LLM for market fit score...")
        market_fit_result = await self._call_llm_for_score(self.market_fit_prompt, processed_pitch_text)
        scores['components']['market_fit'] = market_fit_result

        # --- Originality Score (Vector Embedding + Similarity) ---
        print("NLPProcessor: Calculating originality score...")
        try:
            # Simulate a corpus of existing pitches (in a real system, this comes from a Vector DB)
            existing_pitches_corpus = [
                "Our decentralized finance protocol revolutionizes lending and borrowing on blockchain.",
                "AI-powered medical diagnostics for early disease detection using patient data.",
                "A platform connecting artists and fans in the metaverse through NFTs.",
                "Revolutionizing retail with AR/VR shopping experiences.",
                "Building a new social network focused on privacy and user ownership of data.",
                "A sustainable energy solution leveraging advanced solar panel technology.",
            ]
            pitch_embedding = self.sentence_model.encode(processed_pitch_text, convert_to_tensor=True)
            corpus_embeddings = self.sentence_model.encode(existing_pitches_corpus, convert_to_tensor=True)

            similarities = cosine_similarity(pitch_embedding.unsqueeze(0), corpus_embeddings)
            max_similarity = np.max(similarities)
            # Higher similarity means less original. Scale to 1-10.
            # A perfect match (similarity 1) means score 1. No similarity (similarity 0) means score 10.
            scores['components']['originality'] = {
                'score': max(1, int(10 - (max_similarity * 9))), # Scale from 1 to 10
                'reasoning': f"Pitch similarity to existing concepts: {max_similarity:.2f}. Lower similarity indicates higher originality."
            }
        except Exception as e:
            print(f"NLPProcessor: Error calculating originality score: {e}")
            scores['components']['originality'] = {'score': 0, 'reasoning': f"Error: {e}"}


        # --- Calculate Overall Score ---
        # Simple average for now; later can be weighted or more complex.
        total_score_sum = 0
        num_scored_components = 0
        for comp in ['clarity', 'team_strength', 'market_fit', 'originality']:
            if 'score' in scores['components'][comp]:
                total_score_sum += scores['components'][comp]['score']
                num_scored_components += 1

        if num_scored_components > 0:
            scores['overall_score'] = round(total_score_sum / num_scored_components)
        else:
            scores['overall_score'] = 0

        print(f"NLPProcessor: Analysis complete for pitch {pitch_id}. Overall Score: {scores['overall_score']}")
        return scores

# Example Usage (for testing the NLPProcessor directly)
async def test_nlp_processor():
    processor = NLPProcessor()

    # Create dummy files for testing
    dummy_pitch_content_good = """
    Our startup, Quantum Leap Solutions, aims to revolutionize the supply chain industry using a novel blend of AI and quantum computing.
    The team consists of Dr. Alice Smith, a leading expert in quantum algorithms, and Mr. Bob Johnson, a seasoned supply chain veteran with 15 years of experience at global logistics firms.
    We identified a critical bottleneck in real-time inventory management, causing billions in losses annually. Our solution provides predictive analytics with unparalleled accuracy, reducing waste by 30%.
    The market for supply chain optimization is growing rapidly, with a projected value of $50 billion by 2030. We have secured early partnerships with two major manufacturing companies.
    """
    with open("dummy_pitch_good.txt", "w") as f:
        f.write(dummy_pitch_content_good)

    dummy_pitch_content_poor = """
    We have a product. It does stuff. People will like it. Our team is good. We need money.
    """
    with open("dummy_pitch_poor.txt", "w") as f:
        f.write(dummy_pitch_content_poor)

    print("--- Analyzing dummy_pitch_good.txt ---")
    scores_good = await processor.analyze_pitch(pitch_id="pitch_001", file_path="dummy_pitch_good.txt")
    print(json.dumps(scores_good, indent=2))

    print("\n--- Analyzing dummy_pitch_poor.txt ---")
    scores_poor = await processor.analyze_pitch(pitch_id="pitch_002", file_path="dummy_pitch_poor.txt")
    print(json.dumps(scores_poor, indent=2))

    # Clean up dummy files
    os.remove("dummy_pitch_good.txt")
    os.remove("dummy_pitch_poor.txt")

if __name__ == "__main__":
    asyncio.run(test_nlp_processor())

