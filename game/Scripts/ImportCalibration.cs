using Godot;
using System.Text.Json;

namespace YokaiDominion;

/// <summary>Actual native .glb import, skin/rig/morph checks, animation sampling and optional screenshot.</summary>
public partial class ImportCalibration : Node3D
{
    private static IEnumerable<Node> Descendants(Node node)
    {
        yield return node;
        foreach(Node child in node.GetChildren()) foreach(Node nested in Descendants(child)) yield return nested;
    }
    private static void Require(bool condition,string message)
    { if(!condition) throw new InvalidOperationException(message); }
    public override async void _Ready()
    {
        try
        {
            string[] args=OS.GetCmdlineUserArgs();
            string? reportPath=args.FirstOrDefault(s=>s.StartsWith("--report=",StringComparison.Ordinal))?[9..];
            string? capturePath=args.FirstOrDefault(s=>s.StartsWith("--capture=",StringComparison.Ordinal))?[10..];
            bool headless=DisplayServer.GetName()=="headless";
            Require(!(headless&&capturePath!=null),"A rendered capture requires a display.");
            var packed=GD.Load<PackedScene>("res://Assets/Calibration/calibration.glb");
            Require(packed!=null,"Missing imported calibration GLB. Run the Blender asset workflow first.");
            Node model=packed!.Instantiate(); AddChild(model);
            await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
            var nodes=Descendants(model).ToArray();
            var skeleton=nodes.OfType<Skeleton3D>().FirstOrDefault();
            var skinned=nodes.OfType<MeshInstance3D>().FirstOrDefault(m=>m.Skin!=null&&m.Mesh!=null);
            var player=nodes.OfType<AnimationPlayer>().FirstOrDefault();
            Require(skeleton!=null&&skeleton.GetBoneCount()>=3,"Skeleton lost during native import.");
            Require(skinned!=null&&skinned.Skin.GetBindCount()>=2,"Skin binding lost during native import.");
            Require(player!=null,"AnimationPlayer missing.");
            int lower=skeleton!.FindBone("Lower"); Require(lower>=0,"Lower joint name missing.");
            int morph=skinned!.FindBlendShapeByName("JointVolumeCorrective"); Require(morph>=0,"Corrective morph name missing.");
            var resolved=skinned.GetNodeOrNull<Skeleton3D>(skinned.Skeleton);
            Require(resolved==skeleton,"Mesh skeleton path does not resolve to imported rig.");
            string? clip=player!.GetAnimationList().FirstOrDefault(n=>n!="RESET"); Require(clip!=null,"No usable animation clip.");
            var animation=player.GetAnimation(clip!);
            Require(animation.Length>0.8&&animation.Length<1.2,$"Unexpected animation duration {animation.Length}");
            player.ProcessMode=ProcessModeEnum.Disabled;
            player.Play(clip!); player.Seek(0,true); player.Advance(0);
            await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
            Quaternion restRotation=skeleton.GetBonePoseRotation(lower);
            float restMorph=skinned.GetBlendShapeValue(morph);
            player.Seek(animation.Length/2,true); player.Advance(0);
            await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
            Quaternion bentRotation=skeleton.GetBonePoseRotation(lower);
            float bentMorph=skinned.GetBlendShapeValue(morph);
            float bendRadians=restRotation.AngleTo(bentRotation);
            Require(bendRadians>1.1f&&bendRadians<1.5f,$"Expected approximately 75 degree bend, got {bendRadians} radians.");
            Require(restMorph<0.05f&&bentMorph>0.9f,$"Corrective animation not applied: {restMorph} -> {bentMorph}");
            BuildStage();
            if(capturePath!=null)
            {
                await ToSignal(RenderingServer.Singleton,RenderingServer.SignalName.FramePostDraw);
                using var image=GetViewport().GetTexture().GetImage();
                string full=System.IO.Path.GetFullPath(capturePath);
                System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(full)!);
                Require(image.SavePng(full)==Error.Ok,"Failed to save imported-asset screenshot.");
            }
            var report=new {
                passed=true,engine=Engine.GetVersionInfo()["string"].AsString(),headless,
                bones=Enumerable.Range(0,skeleton.GetBoneCount()).Select(skeleton.GetBoneName).ToArray(),
                skinBindCount=skinned.Skin.GetBindCount(),blendShapes=skinned.GetBlendShapeCount(),clip,durationSeconds=animation.Length,
                bendRadians,restMorph,bentMorph,renderedCapture=capturePath!=null,
                limitation="Calibration fixture only. Not character anatomy, full-body motion, cloth contact, or target-GPU performance."
            };
            string json=JsonSerializer.Serialize(report,new JsonSerializerOptions {WriteIndented=true});
            GD.Print(json);
            if(reportPath!=null)
            {
                string full=System.IO.Path.GetFullPath(reportPath);
                System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(full)!);
                System.IO.File.WriteAllText(full,json);
            }
            GD.Print("YOKAI_NATIVE_ASSET_IMPORT_PASS"); GetTree().Quit();
        }
        catch(Exception e) {GD.PushError(e.ToString()); GetTree().Quit(1);}
    }
    private void BuildStage()
    {
        var env=new WorldEnvironment {Environment=new Godot.Environment {
            BackgroundMode=Godot.Environment.BGMode.Color,BackgroundColor=new(0.045f,0.055f,0.075f),
            AmbientLightSource=Godot.Environment.AmbientSource.Color,AmbientLightColor=new(0.7f,0.8f,1),AmbientLightEnergy=0.5f}};
        AddChild(env);
        AddChild(new DirectionalLight3D {RotationDegrees=new(-35,-25,0),LightEnergy=1.1f});
        var camera=new Camera3D {Current=true,Projection=Camera3D.ProjectionType.Orthogonal,Size=1.3f,Position=new(0.9f,0.85f,2.2f)};
        AddChild(camera); camera.LookAt(new Vector3(-0.12f,0.38f,0));
        var canvas=new CanvasLayer(); AddChild(canvas);
        var label=new Label {Position=new(28,24),Text="YOKAI DOMINION  /  BLENDER TO GODOT\nImported skeleton, skin, animation and corrective morph\nCalibration fixture - not the character model"};
        label.AddThemeFontSizeOverride("font_size",20); canvas.AddChild(label);
    }
}
