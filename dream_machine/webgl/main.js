「globals」

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

const PlaceHolderTexture = function() {
	let Handle = gl.createTexture();
	gl.bindTexture(gl.TEXTURE_2D, Handle);
	gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 255]));
	return Handle;
};

const InitialSetup = function() {
「initial_setup_hook」
};

const Renderer = {
「renderers」
};

const DrawFrame = function(FrameIndex, CurrentTime, DeltaTime) {
	if (WindowIsDirty) {
		WindowResized();
		WindowIsDirty = false;
	}
	gl.viewport(0, 0, ScreenWidth, ScreenHeight);
「draw_frame_hook」
};

const WindowResized = function() {
「resize_hook」
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
