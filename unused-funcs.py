import os
from typing import List

def find_funcs(lines: List[str]) -> List[str]:
    """`lines` are all the lines of code. The function will go through it and find all function definitions,
       putting each function name into the list that's returned."""
    funcs: List[str] = []
    for code_line in lines:
        words = code_line.split()
        if not words or words[0] != 'def':
            continue
        assert '(' in words[1]
        funcs.append(words[1].split('(')[0])
    return funcs

def num_times_func_referenced(lines: List[str], func: str) -> int:
    """Note that this doesn't include the function's definition."""
    num_ref = sum(1 for line in lines if func in line) - 1
    assert num_ref >= 0
    return num_ref

def main():
    lines: List[str] = []
    for filename in os.listdir():
        if not filename.endswith(".py") or filename == "tests.py":
            continue
        with open(filename) as file:
            lines.extend(file.read().splitlines())
    print("Unused functions:")
    for func in find_funcs(lines):
        if (num_ref := num_times_func_referenced(lines, func)) == 0:
            print(f"{func} is unused")
        elif num_ref == 1:
            print(f"{func} is only used once.")

if __name__ == '__main__':
    main()
else:
    raise ImportError("This module is not meant to be imported.")