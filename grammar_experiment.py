
from parser_experiment import *
from graffeine.templates.OpenGL import *


class Grammar:
    def __init__(self, parser:Parser):
        self.comments:List[TokenComment] = []
        self.parser = parser
        self.structs:Dict[str, StructType] = {}
        self.interfaces:Dict[str, StructType] = {}
        #self.draws = {}
        #self.handles = {}
        #self.renderers = {}

    def validate_schema(self, expr:TokenList, **schema):
        head = expr.car()
        tail = expr.cdr()
        if len(expr.tokens) != len(schema.keys()) and not "vargs" in schema:
            self.error(f"Expected {len(schema.keys())} items, got {len(expr.tokens)}", expr)
        for hint_name, expected in schema.items():
            if hint_name == "vargs":
                assert(list(schema.keys())[-1] == "vargs")
                if expected is None:
                    break
                while head is not None:
                    head = cast(Token, head)
                    if type(head) is not expected:
                        self.error(f"Expected {expected.__name__}, got {type(head).__name__}", head)
                    head = tail.car()
                    tail = tail.cdr()
                break
            else:
                head = cast(Token, head)
                if type(head) is not expected:
                    self.error(f"Expected {hint_name} to be {expected.__name__}, got {type(head).__name__}", head)
                head = tail.car()
                tail = tail.cdr()

    def process_struct(self, name:str, args:TokenList) -> StructType:
        members = {}
        self.validate_schema(args, vargs=TokenList)
        for member in args:
            member = cast(TokenList, member)
            self.validate_schema(member, type_name=TokenWord, member_name=TokenWord)
            type_name, member_name = member.tokens
            if str(member_name) in members:
                self.error(f"Duplicate variable name within struct", member_name)
            members[str(member_name)] = self.find_type(type_name)
        return StructType(name, **members)

    def dispatch_command(self, callback:str, instance:str, args:TokenList):
        if callback == "struct":
            if self.structs.get(instance) is not None:
                self.error("Cannot have multiple structs with the same name", args)
            self.structs[instance] = self.process_struct(instance, args)
        elif callback == "interface":
            if self.interfaces.get(instance) is not None:
                self.error("Cannot have multiple interfaces with the same name", args)
            self.interfaces[instance] = self.process_struct(instance, args)
        elif callback == "defdraw":
            pass
        elif callback == "defhandle":
            self.validate_schema(args, handle=TokenWord)
            pass
        elif callback == "renderer":
            pass
        else:
            self.error(f"Unknown command {callback}", args)

    def process(self, tokens:Sequence[Token]):
        for token in tokens:
            if type(token) is TokenComment:
                self.comments.append(cast(TokenComment, token))
            else:
                assert(type(token) is TokenList)
                token = cast(TokenList, token)
                self.validate_schema(token, command=TokenWord, name=TokenWord, vargs=None)
                callback = cast(Token, token.car())
                args = token.cdr()
                instance = cast(Token, token.cdr().car())
                self.dispatch_command(str(callback), str(instance), args.cdr())

    def find_type(self, type_name:TokenWord) -> Optional[GlslType]:
        found = glsl_builtins.get(type_name.word) or self.structs.get(type_name.word)
        if not found:
            self.error(f"No such GLSL builtin type or struct \"{type_name.word}\"", type_name)
        return found

    def error(self, hint:str, token:Token):
        self.parser.error(hint, *token.pos(), *token.pos())


if __name__ == "__main__":
    parser = Parser()
    parser.open("example.data")
    tokens = parser.parse()
    grammar = Grammar(parser)
    grammar.process(tokens)
    import pdb; pdb.set_trace()
