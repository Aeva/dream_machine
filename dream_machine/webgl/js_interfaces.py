
# Copyright 2020 Aeva Palecek
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from ..opengl.glsl_types import *
from ..syntax.abstract import Program, PipelineInput, Buffer, Struct


upload_variants = {
    "bool" : "1i",
    "int" : "1i",
    "uint" : "1i",
    "float" : "1f",
    "bvec2" : "2i",
    "bvec3" : "3i",
    "bvec4" : "4i",
    "ivec2" : "2i",
    "ivec3" : "3i",
    "ivec4" : "4i",
    "uvec2" : "2i",
    "uvec3" : "3i",
    "uvec4" : "4i",
    "vec2" : "2f",
    "vec3" : "3f",
    "vec4" : "4f",
    "mat2" : "Matrix2f",
    "mat3" : "Matrix3f",
    "mat4" : "Matrix4f",
}


class UploadUniform(SyntaxExpander):
    template = 'gl.uniform「variant」v(gl.getUniformLocation(ShaderPrograms[「program:int」], "「name」"), UploadData["「name」"]);'

    def __init__(self, program:int, member_name:str, member_type:GlslType):
        SyntaxExpander.__init__(self)
        if type(member_type) in (ScalarType, VectorType, MatrixType):
            self.program = program
            self.name = member_name
            self.variant = upload_variants[member_type.name]
        else:
            raise NotImplementedError("uploading uniform array and or struct fields")


class UploadUniformBlock(SyntaxExpander):
    template = """
"「name」" : function (UploadData) {
「wrapped」
},
""".strip()
    indent = ("wrapped",)

    def __init__(self, env:Program, buffer:Buffer, struct:StructType):
        SyntaxExpander.__init__(self)
        self.name = buffer.name

        programs = []
        for pipeline in env.pipelines.values():
            for input in pipeline.uniforms:
                if input.buffer == buffer:
                    programs.append(pipeline.index)

        wrapped:List[Union[str, SyntaxExpander]] = []
        for program in programs:
            wrapped.append(f"gl.useProgram(ShaderPrograms[{program}]);")
            for member in struct.members.items():
                wrapped.append(UploadUniform(program, *member))

        self.wrapped = wrapped
