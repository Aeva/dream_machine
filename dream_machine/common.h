
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


#include <string>


#define RETURN_ON_FAIL(hint, hr) \
if (FAILED(hr)) \
{\
	std::cout << "Failed: " << hint << "\n"; \
return 1; \
}


std::string SquashW(const wchar_t* Bluuurg)
{
	std::string NewString;
	while (*Bluuurg)
	{
		if ((*Bluuurg) <= 255)
		{
			NewString.push_back((char)(*Bluuurg));
		}
		else
		{
			NewString.push_back('?');
		}
		Bluuurg++;
	}
	return NewString;
}


inline void HaltAndCatchFire()
{
	__fastfail(7);
}


inline std::string DecodeBase64(const char* Encoded)
{
	uint16_t Acc = 0;
	size_t AccSize = 0;
	std::string Decoded;
	while (true)
	{
		int Value = 0;
		const char Cursor = *Encoded;
		if (Cursor == 0 || Cursor == '=') break;
		else if (Cursor == '+') Value = 62;
		else if (Cursor == '/') Value = 63;
		else if (Cursor >= 'a') Value = ((int)Cursor) - 97 + 26;
		else if (Cursor >= 'A') Value = ((int)Cursor) - 65;
		else if (Cursor >= '0') Value = ((int)Cursor) - 48 + 52;
		Acc = (Acc << 6) | Value;
		AccSize += 6;
		if (AccSize >= 8)
		{
			size_t Shift = AccSize - 8;
			Decoded.push_back((char)((Acc >> Shift) & 0xFF));
			AccSize -= 8;
		}
		Encoded++;
	}
	return Decoded;
}
