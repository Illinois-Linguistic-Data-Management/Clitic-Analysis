import sys
import os
import csv

# Add the directory containing tagged_cha_reader to the Python path
module_path = '/Users/danieltregubenko/Desktop/tagged-transcript-processing-main'
if module_path not in sys.path:
    sys.path.append(module_path)

# Now you can import the tagged_cha_reader module
import tagged_cha_reader

def contains_clitic_pronoun(tokens):
    """
    Checks if the given list of tokens contains clitic pronouns either before the first verb
    or attached to the second verb.
    """
    clitic_pronouns = {"me", "te", "se", "lo", "la", "le", "les"}
    combined_clitics = {f'{cl1}{cl2}' for cl1 in clitic_pronouns for cl2 in clitic_pronouns}

    for token in tokens:
        word, pos = token.split('.')
        if pos == 'PRON' and word in clitic_pronouns:
            return True, word, "proclitic"
        if pos == 'VERB':
            # Check if clitic is attached to the verb
            verb = word
            for clitic in clitic_pronouns.union(combined_clitics):
                if verb.endswith(clitic):
                    return True, verb, "enclitic"
    return False, None, None

def has_two_verbs_with_gap(tokens):
    """
    Checks if there are two verbs in the given list of tokens.
    The verbs can be next to each other or have specific allowed words between them.
    """
    allowed_gaps = {
        1: {"a", "que", "dando"},
        2: {"a a", "de que"}
    }

    verb_positions = [i for i, token in enumerate(tokens) if token.split('.')[-1] == 'VERB']
    for i in range(len(verb_positions) - 1):
        gap_size = verb_positions[i + 1] - verb_positions[i] - 1
        if gap_size in allowed_gaps:
            gap_words = " ".join([tokens[j].split('.')[0] for j in range(verb_positions[i] + 1, verb_positions[i + 1])])
            if gap_words in allowed_gaps[gap_size]:
                return True
    return False

def untag_sentence(sentence):
    """
    Removes the part-of-speech tags from the sentence.
    """
    return " ".join([word.split('.')[0] for word in sentence.split()])

def analyze_variable_clitics(input_dir, output_file):
    """
    Analyzes chat files for sentences with variable clitics and generates a CSV with the results.
    """
    filenames = [f for f in os.listdir(input_dir) if f.endswith('.cha') or f.endswith('.txt')]
    print(f"Found {len(filenames)} files in the directory.")
    results = []

    for file_name in filenames:
        print(f"Processing file: {file_name}")
        file_prefix = os.path.splitext(file_name)[0]
        file_path = os.path.join(input_dir, file_name)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        sentences = [line[5:].strip() for line in lines if line.startswith('%pos:')]
        for sentence in sentences:
            if sentence.strip() == "":
                continue
            tokens = sentence.split()
            if has_two_verbs_with_gap(tokens):
                contains_clitic, clitic_word, clitic_position = contains_clitic_pronoun(tokens)
                if contains_clitic:
                    untagged_sentence = untag_sentence(sentence)
                    print(f"Untagged Sentence: {untagged_sentence}\nClitic Word: {clitic_word}")
                    # Append file_prefix, untagged_sentence, clitic_word, and clitic_position
                    results.append([file_prefix, untagged_sentence, clitic_word, clitic_position])

    print(f"Found {len(results)} sentences with variable clitics.")
    
    # Write results to CSV in the same directory as input
    output_path = os.path.join(input_dir, output_file)
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write header with 'ID', 'Sentence', 'Clitic', and 'Clitic Position'
        writer.writerow(['ID', 'Sentence', 'Clitic', 'Clitic Position'])
        writer.writerows(results)
    print(f"Results written to {output_path}")

def analyze_adjacent_verbs(input_dir, output_file):
    """
    Analyzes chat files specifically for sentences where two verbs are next to each other.
    """
    filenames = [f for f in os.listdir(input_dir) if f.endswith('.cha') or f.endswith('.txt')]
    print(f"Found {len(filenames)} files in the directory for adjacent verbs analysis.")
    results = []

    for file_name in filenames:
        print(f"Processing file: {file_name}")
        file_prefix = os.path.splitext(file_name)[0]
        file_path = os.path.join(input_dir, file_name)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        sentences = [line[5:].strip() for line in lines if line.startswith('%pos:')]
        for sentence in sentences:
            if sentence.strip() == "":
                continue
            tokens = sentence.split()
            verb_positions = [i for i, token in enumerate(tokens) if token.split('.')[-1] == 'VERB']
            adjacent_pairs = []
            for i in range(len(verb_positions) - 1):
                if verb_positions[i + 1] - verb_positions[i] == 1:
                    adjacent_pairs.append((verb_positions[i], verb_positions[i + 1]))
                    print(f"Adjacent Verbs Found: {tokens[verb_positions[i]].split('.')[0]}, {tokens[verb_positions[i + 1]].split('.')[0]}")

            for first_verb_idx, second_verb_idx in adjacent_pairs:
                # Check if there is a clitic before the first verb
                if first_verb_idx > 0:
                    clitic_word, clitic_pos = tokens[first_verb_idx - 1].split('.')
                    clitic_pronouns = {"me", "te", "se", "lo", "la", "le", "les"}
                    if clitic_pos == 'PRON' and clitic_word in clitic_pronouns:
                        untagged_sentence = untag_sentence(sentence)
                        print(f"Untagged Sentence: {untagged_sentence}\nClitic Word: {clitic_word}")
                        results.append([file_prefix, untagged_sentence, clitic_word, "proclitic"])
                # Check if the second verb has a clitic attached
                verb2_word, verb2_pos = tokens[second_verb_idx].split('.')
                combined_clitics = {f'{cl1}{cl2}' for cl1 in clitic_pronouns for cl2 in clitic_pronouns}
                for clitic in clitic_pronouns.union(combined_clitics):
                    if verb2_word.endswith(clitic):
                        untagged_sentence = untag_sentence(sentence)
                        print(f"Untagged Sentence: {untagged_sentence}\nClitic Word: {verb2_word}")
                        results.append([file_prefix, untagged_sentence, verb2_word, "enclitic"])
                        break

    print(f"Found {len(results)} sentences with adjacent verbs having variable clitics.")
    
    # Write results to CSV in the same directory as input
    output_path = os.path.join(input_dir, output_file)
    with open(output_path, 'a', newline='', encoding='utf-8') as csvfile:  # Append to the existing file
        writer = csv.writer(csvfile)
        writer.writerows(results)
    print(f"Results written to {output_path}")

# Update the input directory path to the correct one
input_dir = '/Users/danieltregubenko/Desktop/Clitic'  # Directory containing chat files
output_file = 'variable_clitic_results.csv'

# First pass: original code
analyze_variable_clitics(input_dir, output_file)

# Second pass: analyze adjacent verbs
analyze_adjacent_verbs(input_dir, output_file)
