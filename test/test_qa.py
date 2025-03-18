import pandas as pd
from hey_steve.agent import SteveAgent
from hey_steve.LLMs import OllamaClient
from hey_steve.rag import SteveRAG
import json
from tqdm import tqdm


def ask_questions(
    question_file: str = "data/hf/minecraft-question-answer-700k-indomain.json",
    output_file: str = "data/hf/mc_qa_responses_sample.json"
):
    # Load the QA data and take 1% sample with fixed seed
    mc_qa = pd.read_json(question_file)
    mc_qa = mc_qa.sample(frac=0.001, random_state=0)

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
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(
        f"Processed {len(results)} questions. Results saved to {output_file}")


def eval_questions(
    question_answer_file: str = "data/hf/mc_qa_responses_sample.json",
    output_file: str = "data/hf/mc_qa_responses_eval_sample.json"
):
    mc_qa = pd.read_json(question_answer_file)

    llm_client = OllamaClient(model="qwen2.5:latest")

    with open("hey_steve/prompt_template/llm_judge_rag_prompt.txt", "r") as f:
        pt = f.read()

    results = []
    yes, no, other = 0, 9, 0
    for _, row in tqdm(mc_qa.iterrows(), total=len(mc_qa)):
        user_message = pt.format(
            question=row['question'], golden_answer=row['golden_answer'], my_answer=row['my_answer'])
        try:
            response = llm_client.chat(user_message)
            if response == "Yes":
                yes += 1
            elif response == "No":
                no += 1
            else:
                other += 1
            results.append({
                'question': row['question'],
                'golden_answer': row['golden_answer'],
                'my_answer': row['my_answer'],
                'evaluation': response,
                'source': row['source']
            })
        except Exception as e:
            print(f"Error processing question: {row['question']}")
            print(e)
            continue

    print(f"Yes: {yes}; No: {no}; Other: {other}")

    # Save results to new file
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(
        f"Processed {len(results)} questions. Results saved to {output_file}")


ask_questions()
eval_questions()
