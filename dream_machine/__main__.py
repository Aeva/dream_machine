
import sys
from .syntax.parser import Parser
from .syntax.grammar import validate
from .solver import solve
from .build import build


if __name__ == "__main__":
    try:
        src_path = sys.argv[1]
    except IndexError:
        print("Missing source file path.")
        exit(1)
    parser = Parser()
    parser.open(src_path)
    env = validate(parser)
    solved = solve(env)
    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(solved))
    build("generated.cpp", "user_code.cpp", out_path="generated.exe", debug=True)
