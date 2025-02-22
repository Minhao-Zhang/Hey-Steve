import pandas as pd
from hey_steve.agent import SteveAgent
from hey_steve.LLMs import OllamaClient
from hey_steve.rag import SteveRAG
import json
from tqdm import tqdm

# Load the QA data and take 1% sample with fixed seed
mc_qa = pd.read_json(
    "data/hf/minecraft-question-answer-700k-cleaned-609k.json")
mc_qa = mc_qa.sample(frac=0.01, random_state=0)

# Initialize components
llm_client = OllamaClient(model="llama3.2:latest")
steve_rag = SteveRAG()
steve_agent = SteveAgent(steve_rag, llm_client)

# Process questions and collect responses
results = []
for _, row in tqdm(mc_qa.iterrows(), total=len(mc_qa)):
    question = row['question']
    try:
        response = steve_agent.chat(question)
        results.append({
            'question': question,
            'golden_answer': row['answer'],
            'my_answer': response,
            'source': row['source']
        })
    except Exception as e:
        print(f"Error processing question: {question}")
        print(e)
        continue

# Save results to new file
with open("data/hf/mc_qa_responses_sample.json", "w") as f:
    json.dump(results, f, indent=2)

print(
    f"Processed {len(results)} questions. Results saved to data/hf/mc_qa_responses.json")
