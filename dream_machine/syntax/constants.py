
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


from enum import Enum, auto, IntEnum


class BackendAPI(Enum):
    INVALID = -1
    OpenGL = auto()
    WebGL = auto()


class TextureType(IntEnum):
    """
    For OpenGL, this would represent the "target" param to glCreateTextures etc.
    For D3D12, this would roughly correspond to D3D12_RESOURCE_DIMENSION.
    The numbering of these enums is arbitrary.
    """
    TEXTURE_1D = 1
    TEXTURE_2D = 2
    TEXTURE_3D = 3
    BUFFER = 4
    TEXTURE_CUBE_MAP = 6


class TextureFormats(IntEnum):
    """
    The enum values should correspond to the equivalent values in D3D12's DXGI_FORMAT.
    """

    RGBA_32_FLOAT = 2
    RGBA_32_UINT = 3
    RGBA_32_SINT = 4

    RGB_32_FLOAT = 6
    RGB_32_UINT = 7
    RGB_32_SINT = 8

    RGBA_16_FLOAT = 10
    RGBA_16_UNORM = 11
    RGBA_16_UINT = 12
    RGBA_16_SNORM = 13
    RGBA_16_SINT = 14

    RG_32_FLOAT =  16
    RG_32_UINT = 17
    RG_32_SINT = 18

    RGB_10_A_2_UNORM = 24
    RGB_10_A_2_UINT = 25

    RG_11_B_10_FLOAT = 26

    RGBA_8_UNORM = 28
    RGBA_8_UNORM_SRGB = 29
    RGBA_8_UINT = 30
    RGBA_8_SNORM = 31
    RGBA_8_SINT = 32

    RG_16_FLOAT = 34
    RG_16_UNORM = 35
    RG_16_UINT = 36
    RG_16_SNORM = 37
    RG_16_SINT = 38

    D_32_FLOAT = 40
    R_32_FLOAT = 41
    R_32_UINT = 42
    R_32_SINT = 43

    RG_8_UNORM = 49
    RG_8_UINT = 50
    RG_8_SNORM = 51
    RG_8_SINT = 52

    R_16_FLOAT = 54
    D_16_UNORM = 55
    R_16_UNORM = 56
    R_16_UINT = 57
    R_16_SNORM = 58
    R_16_SINT = 59

    R_8_UNORM = 61
    R_8_UINT = 62
    R_8_SNORM = 63
    R_8_SINT = 64
    A_8_UNORM = 65
    R_1_UNORM = 66


DEPTH_TEXTURE_FORMATS = \
(
    TextureFormats.D_32_FLOAT,
    TextureFormats.D_16_UNORM
)


COLOR_TEXTURE_FORMATS = [f for f in TextureFormats if f not in DEPTH_TEXTURE_FORMATS]
