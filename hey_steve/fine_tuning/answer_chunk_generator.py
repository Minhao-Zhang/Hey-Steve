import json
import os
import random
import time
from litellm import completion


def read_and_combine_json_files(directory="data/chunks"):
    combined_list = []
    files = sorted([f for f in os.listdir(directory) if f.endswith(".json")])
    for file in files:
        filepath = os.path.join(directory, file)
        with open(filepath, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                combined_list.extend(data)
            else:
                print(f"Warning: {file} does not contain a list. Skipping.")
    return combined_list


def save_chunks_to_json(chunks, output_path):
    output_dir = os.path.dirname(output_path)

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, "w") as f:
        json.dump(chunks, f, indent=4)


def generate_questions_from_chunks(chunks, prompt_template_path="hey_steve/prompt_template/question_chunk_pair.txt"):
    with open(prompt_template_path, "r") as f:
        prompt_template = f.read()

    questions = []
    formatted_chunks = ""
    for i, chunk in enumerate(chunks):
        formatted_chunks += f"<chunk_{i}> {chunk} </chunk_{i}>\n"

    prompt = prompt_template.format(ten_chunks=formatted_chunks)
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        time.sleep(4)
        response = completion(model="gemini/gemini-2.0-flash",
                              api_key=os.environ['GEMINI_API_KEY'],
                              messages=messages
                              )
        content = response.choices[0].message.content
        # strip ```json ```
        content = content[7:-3]
        questions_dict = json.loads(content)
        questions = [questions_dict[f"question_{i}"]
                     for i in range(len(chunks))]
    except Exception as e:
        print(f"Error generating questions: {e}")
        return None

    return questions


def generate_question_answer_pairs(chunks,
                                   output_dir="data/chunk_question_pairs",
                                   questions_per_file=1000,
                                   questions_per_llm_request=10
                                   ):
    """
    Generates question-answer pairs from chunks, calling LLM in batches and saving to files.

    Args:
        chunks (list): A list of text chunks.
        output_dir (str): The directory to save the question-answer pairs.
        questions_per_file (int): The number of questions to generate before saving to a file.
        questions_per_llm_request (int): The number of questions to generate per LLM request.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    question_answer_pairs = []
    total_questions_generated = 0
    file_index = 14

    for i in range(file_index*100, len(chunks), questions_per_llm_request):
        chunk_group = chunks[i:i + questions_per_llm_request]

        while True:
            try:
                questions = generate_questions_from_chunks(chunk_group)
                if questions:
                    break
            except Exception as e:
                print(f"Error generating questions: {e}. Retrying...")

        for chunk, question in zip(chunk_group, questions):
            question_answer_pairs.append(
                {"chunk": chunk, "question": question})
        total_questions_generated += len(questions)

        print(f"Generated {total_questions_generated} questions so far.")

        if total_questions_generated >= questions_per_file:
            output_file_name = f"cq_{file_index:02d}.json"
            output_file_path = os.path.join(output_dir, output_file_name)
            print(f"Saving question-answer pairs to {output_file_path}")
            save_chunks_to_json(question_answer_pairs, output_file_path)
            question_answer_pairs = []  # Clear the list for the next file
            total_questions_generated = 0
            file_index += 1

    # Save any remaining question-answer pairs
    if question_answer_pairs:
        output_file_name = f"cq_{file_index:02d}.json"
        output_file_path = os.path.join(output_dir, output_file_name)
        print(f"Saving remaining question-answer pairs to {output_file_path}")
        save_chunks_to_json(question_answer_pairs, output_file_path)


if __name__ == "__main__":
    # Load chunks from the JSON file
    with open("data/chunk_question_pairs/all_chunks.json", "r") as f:
        chunks = json.load(f)

    # Generate question-answer pairs
    generate_question_answer_pairs(chunks)

    print("Question-answer pair generation complete.")
