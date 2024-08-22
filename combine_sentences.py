import nltk
from nltk.tokenize import sent_tokenize

# Ensure NLTK data is downloaded
nltk.download('punkt')


def process_json(json_obj, path=None):
    if path is None:
        path = []

    sentences = []

    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if key == '_content':
                # Process _content key: split into sentences and chunks
                for line in value:
                    sentences.extend(split_text_into_chunks(line, path))
            else:
                # Continue traversing the JSON object
                new_path = path + [key]
                sentences.extend(process_json(value, new_path))
    elif isinstance(json_obj, list):
        for item in json_obj:
            sentences.extend(process_json(item, path))
    else:
        # Handle other types (assuming this is not the case here)
        pass

    return sentences


def split_text_into_chunks(text, path):
    # Use NLTK to split text into sentences
    sentences = sent_tokenize(text)

    # Split sentences into chunks of 4 sentences each
    chunks = [sentences[i:i + 4] for i in range(0, len(sentences), 4)]

    # Format each chunk with the path
    return [f"{join_path_with_under(path)}: {' '.join(chunk)}" for chunk in chunks]


def join_path_with_under(path):
    return " under ".join(path)
