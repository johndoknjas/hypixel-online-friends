import glob
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Func:
    name: str
    line_index: int

def find_funcs(lines: List[str]) -> List[Func]:
    """`lines` are all the lines of code. The function will go through it and find all function definitions,
       putting each function name and line index into the list that's returned."""
    funcs: List[Func] = []
    for i, code_line in enumerate(lines):
        words = code_line.split()
        if not words or words[0] != 'def':
            continue
        assert '(' in words[1]
        funcs.append(Func(words[1].split('(')[0], i))
    return funcs

def find_func_references(lines: List[str], func: Func) -> List[int]:
    """Note that this doesn't include the function's definition."""
    return [i for (i, line) in enumerate(lines) if func.name in line and i != func.line_index]

def output_funcs_with_no_arrow(lines: List[str], funcs: List[Func]) -> None:
    print("Functions without a '->':\n")
    for func in funcs:
        if all('->' not in line for line in lines[func.line_index:func.line_index+3]):
            print(f"{func} possibly does not have a '->'")

def main() -> None:
    lines: List[str] = []
    for filename in glob.iglob('**/*.py', recursive=True):
        if not filename.endswith(".py") or filename == "tests.py":
            continue
        with open(filename) as file:
            lines.extend(file.read().splitlines())
    funcs: List[Func] = find_funcs(lines)
    output_funcs_with_no_arrow(lines, funcs)
    funcs_used_once: List[Tuple[Func, int]] = []
    print("\n\nUnused functions:\n")
    for func in funcs:
        references = find_func_references(lines, func)
        if len(references) == 0:
            print(f"******{func} is unused******")
        elif len(references) == 1:
            funcs_used_once.append((func, references[0]))
    funcs_used_once.sort(key=lambda f:
                         ((defined_vs_used := f[0].line_index-f[1]) < 0, -abs(defined_vs_used)),
                         reverse=True)
    print("\n\nFunctions used only once:\n")
    for f in funcs_used_once:
        print(f"{f[0]} is only referenced at line index {f[1]}")

if __name__ == '__main__':
    main()
else:
    raise ImportError("This module shouldn't be imported.")