
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


#include "d3d12_util.h"
#include <iostream>


extern int ScreenWidth;
extern int ScreenHeight;


ComPtr<IDXGIAdapter1> Adapter;
DXGI_ADAPTER_DESC1 AdapterInfo = { 0 };
ComPtr<ID3D12Device> Device;
ComPtr<ID3D12CommandQueue> DirectQueue;
ComPtr<IDXGISwapChain1> SwapChain;
ComPtr<ID3D12DescriptorHeap> RtvDescriptorHeap;
ComPtr<ID3D12Resource> BackBuffers[2];

ComPtr<ID3D12CommandAllocator> CommandAllocators[2];
HANDLE FrameFenceEvent;
ComPtr<ID3D12Fence> FrameFence;
UINT64 FrameFenceValue;


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


int SetupD3D12(size_t RtvHeapSize)
{
	{
		ComPtr<IDXGIFactory4> Factory;
		RETURN_ON_FAIL("CreateDXGIFactory2", CreateDXGIFactory2(0, IID_PPV_ARGS(&Factory)));

		const D3D_FEATURE_LEVEL FeatureLevel = D3D_FEATURE_LEVEL_12_0;
		for (int p = 0; p <= 1 && !Device; ++p)
		{
			const bool SkipIntegrated = p == 0;
			for (UINT a = 0; DXGI_ERROR_NOT_FOUND != Factory.Get()->EnumAdapters1(a, &Adapter); ++a)
			{
				DXGI_ADAPTER_DESC1 CandidateDesc;
				Adapter->GetDesc1(&CandidateDesc);
				if (CandidateDesc.Flags & DXGI_ADAPTER_FLAG_SOFTWARE)
				{
					continue;
				}
				else if (SUCCEEDED(D3D12CreateDevice(Adapter.Get(), FeatureLevel, _uuidof(ID3D12Device), nullptr)))
				{
					ComPtr<ID3D12Device> CandidateDevice;
					if (SUCCEEDED(D3D12CreateDevice(Adapter.Get(), FeatureLevel, IID_PPV_ARGS(&CandidateDevice))));
					{
						D3D12_FEATURE_DATA_ARCHITECTURE Architecture;
						CandidateDevice->CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE, &Architecture, sizeof(Architecture));
						if (Architecture.UMA && SkipIntegrated)
						{
							continue;
						}
						else
						{
							std::cout << "Using GPU: " << SquashW(CandidateDesc.Description) << "\n";
							AdapterInfo = CandidateDesc;
							Device = CandidateDevice;
							break;
						}
					}
				}
			}
		}
		if (!Device)
		{
			std::cout << "No suitable GPU found.\n";
			return 1;
		}
		{
			D3D12_COMMAND_QUEUE_DESC Desc = {};
			Desc.Type = D3D12_COMMAND_LIST_TYPE_DIRECT;
			RETURN_ON_FAIL("CreateCommandQueue", Device->CreateCommandQueue(&Desc, IID_PPV_ARGS(&DirectQueue)));
		}
		{
			DXGI_SWAP_CHAIN_DESC1 SwapChainDesc = {};
			SwapChainDesc.BufferCount = 2;
			SwapChainDesc.Width = ScreenWidth;
			SwapChainDesc.Height = ScreenHeight;
			SwapChainDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
			SwapChainDesc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
			SwapChainDesc.SwapEffect = DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL;
			SwapChainDesc.SampleDesc.Count = 1;

			RETURN_ON_FAIL("CreateSwapChainForHwnd", Factory->CreateSwapChainForHwnd(
				DirectQueue.Get(),
				GetActiveWindow(),
				&SwapChainDesc,
				nullptr,
				nullptr,
				&SwapChain
			));
		}

		RETURN_ON_FAIL("MakeWindowAssociation", Factory->MakeWindowAssociation(GetActiveWindow(), DXGI_MWA_NO_ALT_ENTER));
	}

	{
		D3D12_DESCRIPTOR_HEAP_DESC HeapDesc = {};
		HeapDesc.NumDescriptors = RtvHeapSize;
		HeapDesc.Type = D3D12_DESCRIPTOR_HEAP_TYPE_RTV;
		RETURN_ON_FAIL("CreateDescriptorHeap RTV", Device->CreateDescriptorHeap(&HeapDesc, IID_PPV_ARGS(&RtvDescriptorHeap)));

		const UINT DescriptorSize = Device->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_RTV);
		D3D12_CPU_DESCRIPTOR_HANDLE Handle(RtvDescriptorHeap->GetCPUDescriptorHandleForHeapStart());
		for (int i = 0; i < 2; ++i)
		{
			SwapChain->GetBuffer(i, IID_PPV_ARGS(&BackBuffers[i]));
			Device->CreateRenderTargetView(BackBuffers[i].Get(), nullptr, Handle);
			Handle.ptr += DescriptorSize;

			Device->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT, IID_PPV_ARGS(&CommandAllocators[i]));
		}
	}

	{
		Device->CreateFence(FrameFenceValue++, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&FrameFence));
		FrameFenceEvent = CreateEvent(nullptr, false, false, nullptr);
	}

	return 0;
}

