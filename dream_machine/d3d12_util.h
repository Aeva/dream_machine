
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


#include <wrl.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <string>

using Microsoft::WRL::ComPtr;


extern ComPtr<IDXGIAdapter1> Adapter;
extern DXGI_ADAPTER_DESC1 AdapterInfo;
extern ComPtr<ID3D12Device> Device;
extern ComPtr<ID3D12CommandQueue> DirectQueue;
extern ComPtr<IDXGISwapChain1> SwapChain;
extern ComPtr<ID3D12DescriptorHeap> RtvDescriptorHeap;
extern ComPtr<ID3D12Resource> BackBuffers[2];
extern ComPtr<ID3D12CommandAllocator> CommandAllocators[2];


#define RETURN_ON_FAIL(hint, hr) \
if (FAILED(hr)) \
{\
	std::cout << "Failed: " << hint << "\n"; \
return 1; \
}


std::string SquashW(const wchar_t* Bluuurg);


int SetupD3D12(size_t RtvHeapSize);
