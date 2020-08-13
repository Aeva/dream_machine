"use strict";

let UserVars = {
	"MiscVar" : 2048,
}
let CurrentRenderer = 0;
let gl = null;

(function() {
	﻿let Shaders = new Array(3);
	let ShaderPrograms = new Array(2);
	let TextureHandles = new Array(2);
	let FrameBufferHandles = new Array(2);

	let ScreenWidth = null;
	let ScreenHeight = null;

	const CompileShader = function(Source, ShaderType) {
		const Handle = gl.createShader(ShaderType);
		gl.shaderSource(Handle, Source);
		gl.compileShader(Handle);
		if (!gl.getShaderParameter(Handle, gl.COMPILE_STATUS)) {
			const ErrorMsg = gl.getShaderInfoLog(Handle);
			console.info(Source);
			console.info(ErrorMsg)
			throw new Error("Shader Failed to Compile!?!");
		}
		return Handle;
	};

	const LinkShaders = function(Shaders) {
		const Handle = gl.createProgram();
		Shaders.forEach(Shader => gl.attachShader(Handle, Shader));
		gl.linkProgram(Handle);
		const InfoLog = gl.getProgramInfoLog(Handle);
		if (InfoLog) {
			console.warn(InfoLog);
		}
		if (!gl.getProgramParameter(Handle, gl.LINK_STATUS)) {
			throw new Error("Shader Failed to Link!?!");
		}
		return Handle;
	};

	let Upload = {
		"WindowParams" : function (UploadData) {
			gl.useProgram(ShaderPrograms[0]);
			gl.uniform4fv(gl.getUniformLocation(ShaderPrograms[0], "WindowSize"), UploadData["WindowSize"]);
			gl.uniform4fv(gl.getUniformLocation(ShaderPrograms[0], "WindowScale"), UploadData["WindowScale"]);
			gl.uniform1fv(gl.getUniformLocation(ShaderPrograms[0], "ElapsedTime"), UploadData["ElapsedTime"]);
			gl.useProgram(ShaderPrograms[1]);
			gl.uniform4fv(gl.getUniformLocation(ShaderPrograms[1], "WindowSize"), UploadData["WindowSize"]);
			gl.uniform4fv(gl.getUniformLocation(ShaderPrograms[1], "WindowScale"), UploadData["WindowScale"]);
			gl.uniform1fv(gl.getUniformLocation(ShaderPrograms[1], "ElapsedTime"), UploadData["ElapsedTime"]);
		},
	};

	const PlaceHolderTexture = function() {
		let Handle = gl.createTexture();
		gl.bindTexture(gl.TEXTURE_2D, Handle);
		gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 255]));
		return Handle;
	};

	const InitialSetup = function() {
		{
			const SplatData = new Float32Array([
				 1.0,  1.0, 0.0,
				-1.0,  1.0, 0.0,
				-1.0, -1.0, 0.0,
				-1.0, -1.0, 0.0,
				 1.0, -1.0, 0.0,
				 1.0,  1.0, 0.0]);
			let vbo = gl.createBuffer();
			gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
			gl.bufferData(gl.ARRAY_BUFFER, SplatData, gl.STATIC_DRAW);
		}
		{
			let ShaderSource = atob("YXR0cmlidXRlIHZlYzMgUG9zaXRpb247CnZvaWQgbWFpbih2b2lkKSB7CiAgZ2xfUG9zaXRpb24gPSB2ZWM0KFBvc2l0aW9uLCAxLjApOwp9");
			Shaders[0] = CompileShader(ShaderSource, gl.VERTEX_SHADER);
		}
		{
			let ShaderSource = atob("Ci8qCglDb3B5cmlnaHQgMjAyMCBBZXZhIFBhbGVjZWsKCglMaWNlbnNlZCB1bmRlciB0aGUgQXBhY2hlIExpY2Vuc2UsIFZlcnNpb24gMi4wICh0aGUgIkxpY2Vuc2UiKTsKCXlvdSBtYXkgbm90IHVzZSB0aGlzIGZpbGUgZXhjZXB0IGluIGNvbXBsaWFuY2Ugd2l0aCB0aGUgTGljZW5zZS4KCVlvdSBtYXkgb2J0YWluIGEgY29weSBvZiB0aGUgTGljZW5zZSBhdAoKCQlodHRwOi8vd3d3LmFwYWNoZS5vcmcvbGljZW5zZXMvTElDRU5TRS0yLjAKCglVbmxlc3MgcmVxdWlyZWQgYnkgYXBwbGljYWJsZSBsYXcgb3IgYWdyZWVkIHRvIGluIHdyaXRpbmcsIHNvZnR3YXJlCglkaXN0cmlidXRlZCB1bmRlciB0aGUgTGljZW5zZSBpcyBkaXN0cmlidXRlZCBvbiBhbiAiQVMgSVMiIEJBU0lTLAoJV0lUSE9VVCBXQVJSQU5USUVTIE9SIENPTkRJVElPTlMgT0YgQU5ZIEtJTkQsIGVpdGhlciBleHByZXNzIG9yIGltcGxpZWQuCglTZWUgdGhlIExpY2Vuc2UgZm9yIHRoZSBzcGVjaWZpYyBsYW5ndWFnZSBnb3Zlcm5pbmcgcGVybWlzc2lvbnMgYW5kCglsaW1pdGF0aW9ucyB1bmRlciB0aGUgTGljZW5zZS4KKi8KCnByZWNpc2lvbiBtZWRpdW1wIGZsb2F0OwoKCnVuaWZvcm0gdmVjNCBXaW5kb3dTaXplOwp1bmlmb3JtIHZlYzQgV2luZG93U2NhbGU7CnVuaWZvcm0gZmxvYXQgRWxhcHNlZFRpbWU7CnVuaWZvcm0gc2FtcGxlcjJEIEZhbmN5VGV4dHVyZTsKCgp2b2lkIG1haW4oKQp7CglmbG9hdCBNYXJnaW4gPSBhYnMoV2luZG93U2l6ZS54IC0gV2luZG93U2l6ZS55KSAqIDAuNTsKCXZlYzIgQ29vcmRzID0gZ2xfRnJhZ0Nvb3JkLnh5OwoJaWYgKFdpbmRvd1NpemUueCA+IFdpbmRvd1NpemUueSkKCXsKCQlDb29yZHMueCAtPSBNYXJnaW47Cgl9CgllbHNlCgl7CgkJQ29vcmRzLnkgLT0gTWFyZ2luOwoJfQoJdmVjMiBVViA9IENvb3JkcyAqIHZlYzIobWF4KFdpbmRvd1NpemUueiwgV2luZG93U2l6ZS53KSk7Cgl2ZWM0IEZnQ29sb3IgPSB0ZXh0dXJlMkQoRmFuY3lUZXh0dXJlLCBVVik7Cgl2ZWMzIEJnQ29sb3IgPSB2ZWMzKDAuMCwgMC41LCAxLjApOwoJZ2xfRnJhZ0NvbG9yID0gdmVjNChtaXgoQmdDb2xvci5yZ2IsIEZnQ29sb3IucmdiLCBGZ0NvbG9yLmEpLCAxLjApOwp9Cg==");
			Shaders[1] = CompileShader(ShaderSource, gl.FRAGMENT_SHADER);
		}
		{
			let ShaderSource = atob("Ci8qCglDb3B5cmlnaHQgMjAyMCBBZXZhIFBhbGVjZWsKCglMaWNlbnNlZCB1bmRlciB0aGUgQXBhY2hlIExpY2Vuc2UsIFZlcnNpb24gMi4wICh0aGUgIkxpY2Vuc2UiKTsKCXlvdSBtYXkgbm90IHVzZSB0aGlzIGZpbGUgZXhjZXB0IGluIGNvbXBsaWFuY2Ugd2l0aCB0aGUgTGljZW5zZS4KCVlvdSBtYXkgb2J0YWluIGEgY29weSBvZiB0aGUgTGljZW5zZSBhdAoKCQlodHRwOi8vd3d3LmFwYWNoZS5vcmcvbGljZW5zZXMvTElDRU5TRS0yLjAKCglVbmxlc3MgcmVxdWlyZWQgYnkgYXBwbGljYWJsZSBsYXcgb3IgYWdyZWVkIHRvIGluIHdyaXRpbmcsIHNvZnR3YXJlCglkaXN0cmlidXRlZCB1bmRlciB0aGUgTGljZW5zZSBpcyBkaXN0cmlidXRlZCBvbiBhbiAiQVMgSVMiIEJBU0lTLAoJV0lUSE9VVCBXQVJSQU5USUVTIE9SIENPTkRJVElPTlMgT0YgQU5ZIEtJTkQsIGVpdGhlciBleHByZXNzIG9yIGltcGxpZWQuCglTZWUgdGhlIExpY2Vuc2UgZm9yIHRoZSBzcGVjaWZpYyBsYW5ndWFnZSBnb3Zlcm5pbmcgcGVybWlzc2lvbnMgYW5kCglsaW1pdGF0aW9ucyB1bmRlciB0aGUgTGljZW5zZS4KKi8KCnByZWNpc2lvbiBtZWRpdW1wIGZsb2F0OwoKCnVuaWZvcm0gdmVjNCBXaW5kb3dTaXplOwp1bmlmb3JtIHZlYzQgV2luZG93U2NhbGU7CnVuaWZvcm0gZmxvYXQgRWxhcHNlZFRpbWU7CnVuaWZvcm0gc2FtcGxlcjJEIFNvbWVUYXJnZXQ7CgoKdm9pZCBtYWluKCkKewoJZmxvYXQgWCA9IHNpbihFbGFwc2VkVGltZSAqIDUwLjAgKyBnbF9GcmFnQ29vcmQueSAqIDAuMSk7CglmbG9hdCBZID0gc2luKEVsYXBzZWRUaW1lICogNTAuMCArIGdsX0ZyYWdDb29yZC54ICogMC4xKTsKCXZlYzIgT2Zmc2V0ID0gdmVjMihYLCBZKSAqIDUuMDsKCXZlYzIgVVYgPSAoZ2xfRnJhZ0Nvb3JkLnh5ICsgT2Zmc2V0KSAqIFdpbmRvd1NpemUuenc7CglnbF9GcmFnQ29sb3IgPSB0ZXh0dXJlMkQoU29tZVRhcmdldCwgVVYpOwp9");
			Shaders[2] = CompileShader(ShaderSource, gl.FRAGMENT_SHADER);
		}
		{
			let Stages = new Array(Shaders[0], Shaders[1]);
			let Handle = ShaderPrograms[0] = LinkShaders(Stages);
			gl.useProgram(Handle);
			const FancyTexture = gl.getUniformLocation(Handle, "FancyTexture");
			if (FancyTexture !== null) {
				gl.uniform1i(FancyTexture, 0);
			}
		}
		{
			let Stages = new Array(Shaders[0], Shaders[2]);
			let Handle = ShaderPrograms[1] = LinkShaders(Stages);
			gl.useProgram(Handle);
			const SomeTarget = gl.getUniformLocation(Handle, "SomeTarget");
			if (SomeTarget !== null) {
				gl.uniform1i(SomeTarget, 0);
			}
		}
		{
			let Handle = TextureHandles[0] = PlaceHolderTexture();
			gl.bindTexture(gl.TEXTURE_2D, Handle, 0);
			let Req = new Image();
			Req.addEventListener("load", function() {
				gl.deleteTexture(TextureHandles[0]);
				let Handle = TextureHandles[0] = gl.createTexture();
				gl.bindTexture(gl.TEXTURE_2D, Handle);
				gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
				gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, Req);
			});
			Req.src = "fnord.png";
		}
		{
			TextureHandles[1] = gl.createTexture();
			gl.bindTexture(gl.TEXTURE_2D, TextureHandles[1]);
			gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, ScreenWidth, ScreenHeight, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
		}
		{
			FrameBufferHandles[0] = gl.createFramebuffer();
			gl.bindFramebuffer(gl.FRAMEBUFFER, FrameBufferHandles[0]);
			gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, TextureHandles[1], 0);
			gl.bindFramebuffer(gl.FRAMEBUFFER, null);
		}
	};

	const Renderer = {
		"Fnord" : function(FrameIndex, CurrentTime, DeltaTime) {
			gl.clearColor(0, 0, 0, 1.0);
			gl.clear(gl.COLOR_BUFFER_BIT);
			gl.clearDepth(0);
			gl.clear(gl.DEPTH_BUFFER_BIT);
			Upload["WindowParams"]({
				"WindowSize" : new Float32Array([ScreenWidth, ScreenHeight, 1.0/ScreenWidth, 1.0/ScreenHeight]),
				"WindowScale" : new Float32Array([1.0, 1.0, 1.0, 1.0]),
				"ElapsedTime" : new Float32Array([CurrentTime * 0.1]),
			});
			{
				{
					let Handle = ShaderPrograms[0];
					gl.useProgram(Handle);
					let AttrCount = gl.getProgramParameter(Handle, gl.ACTIVE_ATTRIBUTES);
					for (let a = 0; a < AttrCount; ++a) {
						let Attr = gl.getActiveAttrib(Handle, a);
						let Index = gl.getAttribLocation(Handle, Attr.name);
						gl.enableVertexAttribArray(Index);
						gl.vertexAttribPointer(Index, 3, gl.FLOAT, false, 0, 0);
					}
				}
				gl.bindFramebuffer(gl.FRAMEBUFFER, FrameBufferHandles[0]);
				gl.activeTexture(gl.TEXTURE0 + 0);
				gl.bindTexture(gl.TEXTURE_2D, TextureHandles[0]);
				gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
				gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
				gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
				gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
				gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, 1);
			}
			{
				{
					let Handle = ShaderPrograms[1];
					gl.useProgram(Handle);
					let AttrCount = gl.getProgramParameter(Handle, gl.ACTIVE_ATTRIBUTES);
					for (let a = 0; a < AttrCount; ++a) {
						let Attr = gl.getActiveAttrib(Handle, a);
						let Index = gl.getAttribLocation(Handle, Attr.name);
						gl.enableVertexAttribArray(Index);
						gl.vertexAttribPointer(Index, 3, gl.FLOAT, false, 0, 0);
					}
				}
				gl.bindFramebuffer(gl.FRAMEBUFFER, null);
				gl.activeTexture(gl.TEXTURE0 + 0);
				gl.bindTexture(gl.TEXTURE_2D, TextureHandles[1]);
				gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
				gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
				gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
				gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
				gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, 1);
			}
		},
	};

	const DrawFrame = function(FrameIndex, CurrentTime, DeltaTime) {
		if (WindowIsDirty) {
			WindowResized();
			WindowIsDirty = false;
		}
		gl.viewport(0, 0, ScreenWidth, ScreenHeight);
		switch (CurrentRenderer) {
		case 0:
			Renderer["Fnord"](FrameIndex, CurrentTime, DeltaTime);
			break;
		default:
			throw new Error("Invalid renderer index: " + CurrentRenderer);
		}
	};

	const WindowResized = function() {
		{
			gl.deleteTexture(TextureHandles[1]);
			TextureHandles[1] = gl.createTexture();
			gl.bindTexture(gl.TEXTURE_2D, TextureHandles[1]);
			gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, ScreenWidth, ScreenHeight, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
		}
		{
			// recreate framebuffer "TextureSplat"
			gl.deleteFramebuffer(FrameBufferHandles[0]);
			FrameBufferHandles[0] = gl.createFramebuffer();
			gl.bindFramebuffer(gl.FRAMEBUFFER, FrameBufferHandles[0]);
			gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, TextureHandles[1], 0);
			gl.bindFramebuffer(gl.FRAMEBUFFER, null);
		}
	};

	let FrameIndex = 0;
	let LastTime = null;
	let WindowIsDirty = true;

	const RenderLoop = function(NowTime) {
		NowTime *= 0.001;
		DrawFrame(FrameIndex++, NowTime, NowTime - LastTime);
		LastTime = NowTime;
		window.requestAnimationFrame(RenderLoop);
	};

	const FirstFrame = function(NowTime) {
		NowTime *= 0.001	;
		DrawFrame(FrameIndex++, NowTime, 0.0);
		LastTime = NowTime;
		window.requestAnimationFrame(RenderLoop);
	};

	let Canvas = null;

	const RescaleCanvas = function() {
		ScreenWidth = document.body.clientWidth;
		ScreenHeight = document.body.clientHeight;
		Canvas.width = ScreenWidth;
		Canvas.height = ScreenHeight;
		WindowIsDirty = true;
	};

	const InstallExtension = function(ExtensionName) {
		if (gl) {
			const ext = gl.getExtension(ExtensionName);
			if (ext) {
				console.info("Using WebGL extension: " + ExtensionName);
				for (const Name in ext) {
					let Rename = Name.replace(/(_{0,1}ANGLE|OES|OVR|EXT|WEBGL)$/, "");
					gl[Rename] = (typeof(ext[Name]) === "function") ? ext[Name].bind(ext) : ext[Name];
				}
			}
			else {
				alert("Missing required WebGL extension: " + ExtensionName);
				gl = null;
			}
		}
	};

	const RequiredExtensions = [
		"ANGLE_instanced_arrays",
		"OES_standard_derivatives"
	];

	addEventListener("load", function() {
		let FullScreenMode = false;
		if (document.body.innerHTML.trim() === "") {
			FullScreenMode = true;
			document.write("<canvas style=\"position:fixed;top:0px;left:0px;\">Your browser does not support WebGL.</canvas>");
			document.close();
		}
		{
			let CanvasSearch = document.getElementsByTagName("canvas");
			if (CanvasSearch.length === 1) {
				Canvas = CanvasSearch[0];
			}
		}

		if (Canvas) {
			if (FullScreenMode) {
				window.addEventListener("resize", RescaleCanvas);
				RescaleCanvas();
			}
			else {
				ScreenWidth = Canvas.width;
				ScreenHeight = Canvas.height;
				WindowIsDirty = true;
			}

			gl = Canvas.getContext("webgl");
			RequiredExtensions.forEach(InstallExtension);

			if (gl) {
				InitialSetup();
				if (typeof(UserSetupCallback) === "function") {
					UserSetupCallback();
				}
				window.requestAnimationFrame(FirstFrame);
			}
		}
	});

})();