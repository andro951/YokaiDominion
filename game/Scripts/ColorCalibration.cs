using Godot;
using System.Text.Json;
using GArray = Godot.Collections.Array;

namespace YokaiDominion;

/// <summary>Render and compare actual pixels, not just material flags.</summary>
public partial class ColorCalibration : Node3D
{
    public override async void _Ready()
    {
        try
        {
            if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("Colour calibration needs a renderer.");
            AddChild(new WorldEnvironment { Environment = new Godot.Environment { BackgroundMode = Godot.Environment.BGMode.Color, BackgroundColor = Colors.Black } });
            var camera = new Camera3D { Projection = Camera3D.ProjectionType.Orthogonal, Size = 2.8f, Position = new(0, 0, 5), Current = true };
            AddChild(camera); camera.LookAt(Vector3.Zero);
            string[] palette = ["777b91", "44475e", "d8ccb8"];
            var reference = new List<MeshInstance3D>();
            var tested = new List<MeshInstance3D>();
            var original = GD.Load<Shader>(CharacterMaterials.ShaderPath);
            var unshaded = new Shader { Code = original.Code.Replace("render_mode cull_disabled;", "render_mode cull_disabled, unshaded;", StringComparison.Ordinal) };
            for (int i = 0; i < palette.Length; i++)
            {
                var srgb = new Color(palette[i]);
                var left = new MeshInstance3D { Position = new(-.55f, .85f - i * .85f, 0), Mesh = new QuadMesh { Size = new(.8f, .55f) }, MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = srgb } };
                AddChild(left); reference.Add(left);
                Vector3[] vertices = [new(-.4f,-.275f,0),new(.4f,-.275f,0),new(.4f,.275f,0),new(-.4f,.275f,0)];
                GArray arrays = []; arrays.Resize((int)Mesh.ArrayType.Max);
                arrays[(int)Mesh.ArrayType.Vertex] = vertices;
                arrays[(int)Mesh.ArrayType.Normal] = Enumerable.Repeat(Vector3.Back,4).ToArray();
                arrays[(int)Mesh.ArrayType.Color] = Enumerable.Repeat(srgb.SrgbToLinear(),4).ToArray();
                arrays[(int)Mesh.ArrayType.Index] = new int[] {0,2,1,0,3,2};
                var mesh = new ArrayMesh(); mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
                var right = new MeshInstance3D { Position = new(.55f,.85f-i*.85f,0), Mesh = mesh, MaterialOverride = new ShaderMaterial { Shader = unshaded } };
                AddChild(right); tested.Add(right);
            }
            for (int i = 0; i < 3; i++) await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
            using var image = GetViewport().GetTexture().GetImage();
            var values = new List<object>();
            for (int i = 0; i < palette.Length; i++)
            {
                var l = camera.UnprojectPosition(reference[i].GlobalPosition); var r = camera.UnprojectPosition(tested[i].GlobalPosition);
                Color a = image.GetPixel((int)l.X,(int)l.Y), b = image.GetPixel((int)r.X,(int)r.Y);
                float error = Math.Max(Math.Abs(a.R-b.R),Math.Max(Math.Abs(a.G-b.G),Math.Abs(a.B-b.B)));
                if (error > 3f/255) throw new InvalidOperationException($"Rendered colour mismatch {palette[i]}: {error}; reference={a}; vertex shader={b}");
                values.Add(new {palette=palette[i],reference=new[]{a.R,a.G,a.B},vertexShader=new[]{b.R,b.G,b.B},maxChannelError=error});
            }
            string? directory = OS.GetCmdlineUserArgs().FirstOrDefault(s=>s.StartsWith("--output=",StringComparison.Ordinal))?[9..];
            if (directory != null)
            {
                System.IO.Directory.CreateDirectory(directory);
                if (image.SavePng(System.IO.Path.Combine(directory,"colour-calibration.png")) != Error.Ok) throw new InvalidOperationException("Could not save calibration image.");
                System.IO.File.WriteAllText(System.IO.Path.Combine(directory,"colour-calibration.json"),JsonSerializer.Serialize(new {passed=true,sourceCommit=System.Environment.GetEnvironmentVariable("GITHUB_SHA"),renderer=RenderingServer.GetCurrentRenderingMethod(),engine=Engine.GetVersionInfo()["string"].AsString(),samples=values},new JsonSerializerOptions{WriteIndented=true}));
            }
            GD.Print("YOKAI_RENDERED_COLOUR_PASS"); GetTree().Quit();
        }
        catch (Exception e) { GD.PushError(e.ToString()); GetTree().Quit(1); }
    }
}
