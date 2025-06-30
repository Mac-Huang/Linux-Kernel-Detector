from pydriller import Repository
import os
import json
from tqdm import tqdm
import re

REPO_PATH = '../linux'
OUTPUT_FILE = './output/linux_bugfix_dataset.jsonl'

TEST_MODE = False  # Set to False to process the full repository

BUGFIX_KEYWORDS = [
    'fix', 'bug', 'leak', 'null', 'overflow', 'error', 'failure',
    'crash', 'panic', 'memory', 'race', 'deadlock', 'corruption',
    'security', 'vulnerability', 'exploit', 'buffer', 'stack'
]

def is_bugfix_commit(msg):
    msg_lower = msg.lower()
    return any(keyword in msg_lower for keyword in BUGFIX_KEYWORDS)

def extract_instruction_from_commit_msg(msg):
    lines = msg.strip().splitlines()
    for line in lines:
        line = line.strip()
        if len(line) < 5 or not any(c.isalpha() for c in line):
            continue
        if line.lower().startswith((
            '[patch]', 'signed-off-by', 'reviewed-by', 'tested-by', 'ack',
            'reported-by', 'cc:', 'co-authored-by', 'patchwork-id',
            'suggested-by', 'fixes:', 'link:', 'cherry picked from commit'
        )):
            continue
        return line
    return msg.strip().splitlines()[0] if msg.strip() else "fix"

def extract_code_context(code, line_number, context_lines=10):
    if not code:
        return ""
    lines = code.split('\n')
    start = max(0, line_number - context_lines)
    end = min(len(lines), line_number + context_lines)
    return '\n'.join(lines[start:end])

def extract_diff_context(diff_text, context_lines=5):
    if not diff_text:
        return ""
    lines = diff_text.split('\n')
    change_lines = [i for i, line in enumerate(lines) if line.startswith('+') or line.startswith('-')]
    if not change_lines:
        return diff_text
    start = max(0, change_lines[0] - context_lines)
    end = min(len(lines), change_lines[-1] + context_lines + 1)
    return '\n'.join(lines[start:end])

def create_dataset_entry(original_code, commit_msg, diff_code):
    return {
        "input": {
            "original code": original_code.strip(),
            "instruction": extract_instruction_from_commit_msg(commit_msg)
        },
        "output": {
            "diff codes": diff_code.strip()
        }
    }

def process_commit(commit):
    entries = []
    if not is_bugfix_commit(commit.msg):
        return entries

    for mod in commit.modified_files:
        if not mod.new_path or not mod.new_path.endswith(('.c', '.h')):
            continue
        if mod.change_type.name != "MODIFY":
            continue
        if not mod.diff or not mod.source_code_before:
            continue

        focused_diff = extract_diff_context(mod.diff)

        diff_lines = mod.diff.split('\n')
        line_numbers = []
        for line in diff_lines:
            if line.startswith('@@'):
                match = re.search(r'@@ -(\d+),?\d* \+\d+,?\d* @@', line)
                if match:
                    line_numbers.append(int(match.group(1)))

        if line_numbers:
            focused_code = extract_code_context(mod.source_code_before, line_numbers[0])
        else:
            focused_code = '\n'.join(mod.source_code_before.split('\n')[:50])

        entry = create_dataset_entry(
            original_code=focused_code,
            commit_msg=commit.msg,
            diff_code=focused_diff
        )
        entries.append(entry)

    return entries

def main():
    if not os.path.exists(REPO_PATH):
        print(f"\u274c Repository not found at: {REPO_PATH}")
        return

    os.makedirs('./output', exist_ok=True)

    print("\ud83d\udd0d Building Linux kernel bug-fix dataset...")
    print(f"\ud83d\udcc1 Repository: {REPO_PATH}")
    print(f"\ud83d\udcce Output: {OUTPUT_FILE}")

    output_file = OUTPUT_FILE.replace('.jsonl', '_test.jsonl') if TEST_MODE else OUTPUT_FILE

    repo = Repository(REPO_PATH)
    dataset_entries = []
    processed_commits = 0
    total_commits = 0
    bugfix_commits = 0

    for commit in tqdm(repo.traverse_commits(), desc="Processing commits"):
        total_commits += 1
        if TEST_MODE and MAX_COMMITS_TEST and total_commits > MAX_COMMITS_TEST:
            break
        if is_bugfix_commit(commit.msg):
            bugfix_commits += 1
            entries = process_commit(commit)
            if entries:
                dataset_entries.extend(entries)
                processed_commits += 1
                if TEST_MODE:
                    print(f"\n\ud83d\udd0d Bug-fix commit {processed_commits}: {commit.hash[:8]}")
                    print(f"\ud83d\udcdd Message: {extract_instruction_from_commit_msg(commit.msg)}")
                    print(f"\ud83d\udcca Files: {len(entries)} entries extracted")
                    print(f"\ud83d\udcc1 Files: {[mod.new_path for mod in commit.modified_files if mod.new_path and mod.new_path.endswith(('.c', '.h'))]}")

    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in dataset_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"\n\u2705 Dataset creation completed!")
    print(f"\ud83d\udcca Total commits processed: {total_commits}")
    print(f"\ud83d\udc1b Bug-fix commits found: {bugfix_commits}")
    print(f"\ud83d\udcdd Commits with valid entries: {processed_commits}")
    print(f"\ud83d\udcdd Total dataset entries: {len(dataset_entries)}")
    print(f"\ud83d\udcce Saved to: {output_file}")

    if dataset_entries:
        print(f"\n\ud83d\udccb Sample dataset entry:")
        sample = dataset_entries[0]
        print(json.dumps(sample, indent=2, ensure_ascii=False)[:800] + "...")
        print(f"\n\ud83d\udcc1 Dataset structure:")
        print(f"   - Input: original code + instruction")
        print(f"   - Output: diff codes")
        print(f"   - Format: JSONL (one JSON object per line)")

if __name__ == "__main__":
    main()