import time
import json
import os
import random
import dotenv
import litellm

# Load environment variables
dotenv.load_dotenv()

# Existing constants
CHUNK_FILE = "data/chunk_question_pairs_new/all_chunks.json"
PROMPT_TEMPLATE_PATH = "hey_steve/prompt_template/generate_chunk_questions.txt"
CACHE_FILE = "data/chunk_question_pairs_new/chunk_question_pairs.json"  # New cache file


def generate_questions(chunk, prompt_template):
    """Generates questions for a given chunk using litellm and deepseek-chat."""
    prompt = prompt_template.format(chunk=chunk)
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    for attempt in range(10):
        try:
            response = litellm.completion(
                model="deepseek/deepseek-chat",
                api_key=os.environ.get("DEEPSEEK_API_KEY"),
                messages=messages
            )
            question_data = json.loads(
                response.choices[0].message.content[7:-3].strip())
            return {chunk: question_data}
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(1)  # Wait for 1 second before retrying
    else:
        print("Failed to generate questions after 10 attempts. Skipping chunk.")
        return {chunk: {}}  # Store empty dict in case of error


def main():
    """Main function to read chunks, generate questions, and store them in a JSON file."""
    # 1. Read chunks from JSON file
    with open(CHUNK_FILE, 'r') as f:
        all_chunks = json.load(f)

    # 2. Read prompt template
    with open(PROMPT_TEMPLATE_PATH, 'r') as f:
        prompt_template = f.read()

    # 3. Shuffle the chunks
    random.shuffle(all_chunks)

    # 4. Generate questions for each chunk and append to the cache file
    # Ensure directory exists
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    # Load existing data if the cache file exists
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            try:
                question_pairs = json.load(f)
            except json.JSONDecodeError:
                question_pairs = {}
    else:
        question_pairs = {}

    processed_count = 0
    skipped_count = 0

    for i, chunk in enumerate(all_chunks):
        # Skip if chunk already exists in cache
        if chunk in question_pairs:
            skipped_count += 1
            print(
                f"Skipping already processed chunk {i+1}/{len(all_chunks)}")
            continue

        new_question_pair = generate_questions(chunk, prompt_template)

        question_pairs.update(new_question_pair)
        processed_count += 1
        print(f"Generated questions for chunk {i+1}/{len(all_chunks)}")

        # Append the updated question_pairs to the cache file
        with open(CACHE_FILE, 'w') as f:
            json.dump(question_pairs, f, indent=4)

        print(f"\nProcessing complete!")
        print(f"Processed {processed_count} new chunks")
        print(f"Skipped {skipped_count} already processed chunks")

    # Append the updated question_pairs to the cache file
    with open(CACHE_FILE, 'w') as f:
        json.dump(question_pairs, f, indent=4)

    print(f"Generated questions stored in {CACHE_FILE}")
    print(f"Generated questions stored in {CACHE_FILE}")


def clear_empty_lines():
    with open(CACHE_FILE, 'r') as f:
        question_pairs: dict = json.load(f)

    to_remove = []
    for k, v in question_pairs.items():
        if len(v) == 0:
            to_remove.append(k)

    for k in to_remove:
        question_pairs.pop(k)

    with open(CACHE_FILE, 'w') as f:
        json.dump(question_pairs, f, indent=4)


if __name__ == "__main__":
    clear_empty_lines()
    main()
