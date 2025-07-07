import json

INPUT_FILE = './output/linux_bugfix_dataset.jsonl'
OUTPUT_FILE = './output/linux_bugfix_prompt_completion.jsonl'

def format_prompt(original_code, instruction):
    return (
        "Given the following original C code:\n"
        f"{original_code.strip()}\n\n"
        "Instruction:\n"
        f"{instruction.strip()}\n\n"
        "Return the diff that fixes it:\n"
    )

def format_completion(diff_code):
    return diff_code.strip()

def convert_dataset(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:

        for line in fin:
            data = json.loads(line)
            original_code = data["input"]["original code"]
            instruction = data["input"]["instruction"]
            diff_code = data["output"]["diff codes"]

            prompt = format_prompt(original_code, instruction)
            completion = format_completion(diff_code)

            new_entry = {
                "prompt": prompt,
                "completion": completion
            }

            fout.write(json.dumps(new_entry, ensure_ascii=False) + '\n')

    print(f"[DONE] Converted dataset saved to: {output_path}")

if __name__ == "__main__":
    convert_dataset(INPUT_FILE, OUTPUT_FILE)
