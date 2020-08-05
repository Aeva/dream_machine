"use strict";

let UserVars = {
	MiscVar : 2048,
}
let CurrentRenderer = 0;
let gl = null;

(function() {
	﻿let Shaders = new Array(2);
	let ShaderPrograms = new Array(1);

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

	const LinkShaders = function(Shaders)
	{
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
			let ShaderSource = atob("Ci8qCglDb3B5cmlnaHQgMjAyMCBBZXZhIFBhbGVjZWsKCglMaWNlbnNlZCB1bmRlciB0aGUgQXBhY2hlIExpY2Vuc2UsIFZlcnNpb24gMi4wICh0aGUgIkxpY2Vuc2UiKTsKCXlvdSBtYXkgbm90IHVzZSB0aGlzIGZpbGUgZXhjZXB0IGluIGNvbXBsaWFuY2Ugd2l0aCB0aGUgTGljZW5zZS4KCVlvdSBtYXkgb2J0YWluIGEgY29weSBvZiB0aGUgTGljZW5zZSBhdAoKCQlodHRwOi8vd3d3LmFwYWNoZS5vcmcvbGljZW5zZXMvTElDRU5TRS0yLjAKCglVbmxlc3MgcmVxdWlyZWQgYnkgYXBwbGljYWJsZSBsYXcgb3IgYWdyZWVkIHRvIGluIHdyaXRpbmcsIHNvZnR3YXJlCglkaXN0cmlidXRlZCB1bmRlciB0aGUgTGljZW5zZSBpcyBkaXN0cmlidXRlZCBvbiBhbiAiQVMgSVMiIEJBU0lTLAoJV0lUSE9VVCBXQVJSQU5USUVTIE9SIENPTkRJVElPTlMgT0YgQU5ZIEtJTkQsIGVpdGhlciBleHByZXNzIG9yIGltcGxpZWQuCglTZWUgdGhlIExpY2Vuc2UgZm9yIHRoZSBzcGVjaWZpYyBsYW5ndWFnZSBnb3Zlcm5pbmcgcGVybWlzc2lvbnMgYW5kCglsaW1pdGF0aW9ucyB1bmRlciB0aGUgTGljZW5zZS4KKi8KCnByZWNpc2lvbiBtZWRpdW1wIGZsb2F0OwoKCgoKCnZvaWQgbWFpbigpCnsKCWdsX0ZyYWdDb2xvciA9IHZlYzQoMC4wLCAwLjUsIDEuMCwgMS4wKTsKfQo=");
			Shaders[1] = CompileShader(ShaderSource, gl.FRAGMENT_SHADER);
		}
		{
			let Stages = new Array(Shaders[0], Shaders[1]);
			ShaderPrograms[0] = LinkShaders(Stages);
		}
	};

	const Renderer = {
		"Test" : function(FrameIndex, CurrentTime, DeltaTime) {
			gl.clearColor(0, 0, 0, 1.0);
			gl.clear(gl.COLOR_BUFFER_BIT);
			gl.clearDepth(0);
			gl.clear(gl.DEPTH_BUFFER_BIT);
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
			Renderer["Test"](FrameIndex, CurrentTime, DeltaTime);
			break;
		default:
			throw new Error("Invalid renderer index: " + CurrentRenderer);
		}
	};

	const WindowResized = function() {

	};

	let FrameIndex = 0;
	let LastTime = null;
	let WindowIsDirty = true;

	const RenderLoop = function(NowTime) {
		DrawFrame(FrameIndex++, NowTime, NowTime - LastTime);
		LastTime = NowTime;
		window.requestAnimationFrame(RenderLoop);
	};

	const FirstFrame = function(NowTime) {
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
		"OES_standard_derivatives",
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