
import os
from graffeine.template_tools import *


if __name__ == "__main__":
    src = \
    [
        cpp_include('<iostream>'),
        cpp_def_fn(
            "int", "main", [],
            [
                cpp_def_var("const char*", "Name", '"Eris"'),
                'std::cout << "Hello " << Name << "!\\n";',
                "return 0;",
            ]),
        "",
    ]
    with open("generated.cpp", "w") as outfile:
        outfile.write("\n".join(src))
    os.system("g++ generated.cpp")
