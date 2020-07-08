
import sys
from .syntax.parser import Parser
from .syntax.grammar import validate
#from .solvers.intermediary import Program
#from .solvers.generator import ProgramSolver
#from .build import build


if __name__ == "__main__":
    try:
        src_path = sys.argv[1]
    except IndexError:
        print("Missing source file path.")
        exit(1)
    parser = Parser()
    parser.open(src_path)

    env = validate(parser)
    import pdb; pdb.set_trace()

    #tokens = parser.parse()
    #validate_grammar(GRAMMAR, parser, tokens)
    #program = Program(parser)
    #program.process(tokens)
    #solved = ProgramSolver(program)
    #with open("generated.cpp", "w", encoding="utf-8") as outfile:
    #    outfile.write(str(solved.expand()))
    #build("generated.cpp", "user_code.cpp", out_path="generated.exe", debug=True)
