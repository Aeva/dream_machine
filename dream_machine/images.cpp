
/*
	Copyright 2020 Aeva Palecek

	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

		http://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License.
*/


#include <iostream>
#include "lodepng.h"
#include "common.h"
#include "images.h"


ImageData ReadPng(const char* Path)
{
	ImageData Image;
	std::vector<unsigned char> Data;
	unsigned Error = lodepng::decode(Data, Image.Width, Image.Height, Path);
	if (Error)
	{
		std::cout \
			<< "Failed to read " << Path << "!\n"
			<< " - Reason: PNG decode error:\n"
			<< " - [" << Error << "] " << lodepng_error_text(Error) << "\n";
		HaltAndCatchFire();
	}
	Image.Data.resize(Data.size());
	int Dst = 0;
	const int RowSize = Image.Width * 4;
	for (int y = Image.Height - 1; y >= 0; --y)
	{
		int Src = RowSize * y;
		for (int x = 0; x < RowSize; ++x)
		{
			Image.Data[Dst] = Data[Src];
			++Dst;
			++Src;
		}
	}
	return Image;
}
