"use strict";


let UserVars = {
	MiscVar : 2048,
}
let CurrentRenderer = 0;
let gl = null;


(function() {
	

	let ScreenWidth = null;
	let ScreenHeight = null;

	const InitialSetup = function() {
		{
		let vao = gl.createVertexArray();
		gl.bindVertexArray(vao);
	}
	}

	const Renderer = {
	
	}

	const DrawFrame = function(FrameIndex, CurrentTime, DeltaTime) {
		if (WindowIsDirty)
		{
			WindowResized();
			WindowIsDirty = false;
		}
		gl.viewport(0, 0, ScreenWidth, ScreenHeight);
		gl.clearColor(0.75, 0.0, 0.6, 1.0);
		gl.clear(gl.COLOR_BUFFER_BIT);

	
	}

	const WindowResized = function() {
	
	}

	let FrameIndex = 0;
	let LastTime = null;
	let WindowIsDirty = true;

	const RenderLoop = function (NowTime) {
		DrawFrame(FrameIndex++, NowTime, NowTime - LastTime);
		LastTime = NowTime;
		window.requestAnimationFrame(RenderLoop);
	}

	const FirstFrame = function (NowTime) {
		DrawFrame(FrameIndex++, NowTime, 0.0);
		LastTime = NowTime;
		window.requestAnimationFrame(RenderLoop);
	}

	let Canvas = null;
	const RescaleCanvas = function () {
		ScreenWidth = document.body.clientWidth;
		ScreenHeight = document.body.clientHeight;
		Canvas.width = ScreenWidth;
		Canvas.height = ScreenHeight;
		WindowIsDirty = true;
	}

	const InstallExtension = function (ExtensionName) {
		if (gl)
		{
			const ext = gl.getExtension(ExtensionName);
			if (ext) {
				console.info("Using WebGL extension: " + ExtensionName);
				for (const Name in ext) {
					let Rename = Name.replace(/(_{0,1}ANGLE|OES|OVR|EXT|WEBGL)$/, "");
					gl[Rename] = (typeof(ext[Name]) === "function") ? ext[Name].bind(ext) : ext[Name];
				}
			}
			else
			{
				alert("Missing required WebGL extension: " + ExtensionName);
				gl = null;
			}
		}
	}

	const RequiredExtensions = [
		"OES_vertex_array_object",
		"ANGLE_instanced_arrays",
		"OES_standard_derivatives",
	];

	addEventListener("load", function() {
		let FullScreenMode = false;
		if (document.body.innerHTML.trim() === "")
		{
			FullScreenMode = true;
			document.write("<canvas style=\"position:fixed;top:0px;left:0px;\">Your browser does not support WebGL.</canvas>");
			document.close();
		}
		{
			let CanvasSearch = document.getElementsByTagName("canvas");
			if (CanvasSearch.length === 1)
			{
				Canvas = CanvasSearch[0];
			}
		}
		if (Canvas);
		{
			if (FullScreenMode)
			{
				window.addEventListener("resize", RescaleCanvas);
				RescaleCanvas();
			}
			else
			{
				ScreenWidth = Canvas.width;
				ScreenHeight = Canvas.height;
				WindowIsDirty = true;
			}

			gl = Canvas.getContext("webgl");
			RequiredExtensions.forEach(InstallExtension);
			if (gl)
			{
				InitialSetup();
				if (typeof(UserSetupCallback) === "function") {
					UserSetupCallback();
				}
				window.requestAnimationFrame(FirstFrame);
			}
		}
	});
})();
