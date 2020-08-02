"use strict";



let CurrentRenderer = 0;
let gl = null;


(function() {
	

	let ScreenWidth = null;
	let ScreenHeight = null;

	let InitialSetup = function() {
	
	}

	let Renderer = {
	
	}

	let DrawFrame = function(FrameIndex, CurrentTime, DeltaTime) {
		if (WindowIsDirty)
		{
			WindowResized();
			WindowIsDirty = false;
		}
		gl.viewport(0, 0, ScreenWidth, ScreenHeight);
		gl.clearColor(0.75, 0.0, 0.6, 1.0);
		gl.clear(gl.COLOR_BUFFER_BIT);

	
	}

	let WindowResized = function() {
	
	}

	let FrameIndex = 0;
	let LastTime = null;
	let WindowIsDirty = true;

	let RenderLoop = function (NowTime) {
		DrawFrame(FrameIndex++, NowTime, NowTime - LastTime);
		LastTime = NowTime;
		window.requestAnimationFrame(RenderLoop);
	}

	let FirstFrame = function (NowTime) {
		DrawFrame(FrameIndex++, NowTime, 0.0);
		LastTime = NowTime;
		window.requestAnimationFrame(RenderLoop);
	}

	let Canvas = null;
	let RescaleCanvas = function () {
		ScreenWidth = document.body.clientWidth;
		ScreenHeight = document.body.clientHeight;
		Canvas.width = ScreenWidth;
		Canvas.height = ScreenHeight;
		WindowIsDirty = true;
	}

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
			InitialSetup();
			if (typeof(UserSetupCallback) === "function") {
				UserSetupCallback();
			}
			window.requestAnimationFrame(FirstFrame);
		}
	});
})();
