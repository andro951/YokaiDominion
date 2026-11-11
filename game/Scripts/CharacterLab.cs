using Godot;
using System.Text.Json;
using Yokai.Tissue;

namespace YokaiDominion;

/// <summary>Actual-character deformation laboratory. Not the finished game/controller.</summary>
public partial class CharacterLab : Node3D
{
    private Skeleton3D rig=null!;
    private AnimationPlayer player=null!;
    private CharacterTissueRegion[] regions=[];
    private CharacterSurface[] surfaces=[];
    private int[] supportBones=[];
    private Transform3D[] inverseRest=[];
    private Camera3D camera=null!;
    private Label label=null!;
    private string clip="";
    private bool ready,validating,physics=true,play;
    private int poseIndex;
    private double clock,jumpTime=-1,clipTime;
    private float yaw=.45f,pitch=.10f,distance=4.4f;
    private static readonly string[] PoseNames=["Neutral","Overhead","Crouch","High kick","Torso twist","Jump pose","Knockdown","Recover"];
    private static IEnumerable<Node> Walk(Node n){yield return n;foreach(Node c in n.GetChildren())foreach(Node d in Walk(c))yield return d;}
    private static void Require(bool c,string message){if(!c)throw new InvalidOperationException(message);}
    private static RigidPose Convert(Transform3D t)
    {
        var q=t.Basis.GetRotationQuaternion();return new(CharacterSurface.ToCore(t.Origin),new Q4(q.X,q.Y,q.Z,q.W));
    }
    private RigidPose Support(int i)=>Convert(rig.GlobalTransform*rig.GetBoneGlobalPose(supportBones[i])*inverseRest[i]);
    public override async void _Ready()
    {
        try
        {
            var args=OS.GetCmdlineUserArgs();validating=args.Contains("--validate");BuildStage();
            var packed=GD.Load<PackedScene>("res://Assets/Character01/character-blockout.glb");Require(packed!=null,"Generate/copy the character asset first (see milestone 002 instructions).");
            var model=packed!.Instantiate<Node3D>();AddChild(model);await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
            var all=Walk(model).ToArray();rig=all.OfType<Skeleton3D>().Single();player=all.OfType<AnimationPlayer>().Single();
            Require(rig.GetBoneCount()>=70,"Full-body rig missing joints.");
            clip=player.GetAnimationList().Single(n=>n!="RESET");player.CallbackModeProcess=AnimationMixer.AnimationCallbackModeProcess.Manual;
            player.Play(clip);Sample(0);await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
            string json=Godot.FileAccess.GetFileAsString("res://Assets/Character01/tissue-regions.json");regions=CharacterTissueAsset.Parse(json).Regions.Select(r=>r.CreateRuntime()).ToArray();
            supportBones=regions.Select(r=>rig.FindBone(r.Definition.Bone)).ToArray();Require(supportBones.All(b=>b>=0),"Tissue support bone missing.");
            inverseRest=supportBones.Select(b=>rig.GetBoneGlobalRest(b).AffineInverse()).ToArray();
            var selected=all.OfType<MeshInstance3D>().Where(m=>m.Name.ToString()=="Body"||m.Name.ToString().StartsWith("ChestDrape",StringComparison.Ordinal)).ToArray();
            Require(selected.Any(m=>m.Name.ToString()=="Body"),"Body mesh missing.");
            surfaces=selected.Select(m=>new CharacterSurface(this,m,rig,regions)).ToArray();
            Require(surfaces.Sum(s=>s.BoundVertices)>300,"Too few actual skin vertices embedded in tissue cages.");
            for(int i=0;i<regions.Length;i++)regions[i].Body.ResetPose(Support(i));
            ready=true;UpdateVisual();if(validating)await Validate(args);
        }
        catch(Exception e){GD.PushError(e.ToString());GetTree().Quit(1);}
    }
    private void Sample(double time){player.Seek(Math.Clamp(time,0,player.GetAnimation(clip).Length),true);player.Advance(0);}
    private void ResetRegions(){for(int i=0;i<regions.Length;i++)regions[i].Body.ResetPose(Support(i));}
    private void Step(double dt)
    {
        clock+=dt;
        if(play){clipTime=(clipTime+dt)%7;Sample(clipTime);}else Sample(poseIndex);
        if(jumpTime>=0)
        {
            jumpTime+=dt;double p=jumpTime/.9;float height=p<1?(float)(1.2*p*(1-p)):0;
            int root=rig.FindBone("Root");rig.SetBonePosePosition(root,rig.GetBonePosePosition(root)+new Vector3(0,height,0));if(p>=1)jumpTime=-1;
        }
        if(physics)for(int i=0;i<regions.Length;i++)regions[i].Body.Step(dt,Support(i));else ResetRegions();
    }
    public override void _PhysicsProcess(double delta)
    {
        if(!ready||validating)return;
        try{Step(1.0/60);UpdateVisual();}catch(Exception e){GD.PushError(e.ToString());ready=false;label.Text="SIMULATION STOPPED: "+e.Message;}
    }
    private void UpdateVisual()
    {
        foreach(var s in surfaces){s.SetPhysics(physics);if(physics)s.Update(true);}
        float motion=physics&&surfaces.Length>0?surfaces.Max(s=>s.MaxDisplacement):0;
        label.Text=$"YOKAI DOMINION / CHARACTER BLOCKOUT\n{PoseNames[poseIndex]} | Tissue {(physics?"ON":"OFF")} | Surface displacement {motion*100:0.0} cm\n1-8 poses   Space jump   P physics   Tab pose study   R reset\nDrag to orbit / wheel zoom. Early topology, weights and materials.";
    }
    public override void _UnhandledInput(InputEvent e)
    {
        if(!ready||validating)return;
        if(e is InputEventMouseMotion m&&Input.IsMouseButtonPressed(MouseButton.Left)){yaw-=m.Relative.X*.006f;pitch=Math.Clamp(pitch+m.Relative.Y*.004f,-.6f,.9f);MoveCamera();}
        if(e is InputEventMouseButton b&&b.Pressed){if(b.ButtonIndex==MouseButton.WheelUp)distance=Math.Max(2.5f,distance-.25f);if(b.ButtonIndex==MouseButton.WheelDown)distance=Math.Min(8,distance+.25f);MoveCamera();}
        if(e is InputEventKey k&&k.Pressed&&!k.Echo)
        {
            if(k.Keycode>=Key.Key1&&k.Keycode<=Key.Key8){poseIndex=(int)k.Keycode-(int)Key.Key1;play=false;Sample(poseIndex);ResetRegions();}
            if(k.Keycode==Key.Space){jumpTime=0;poseIndex=0;play=false;Sample(0);ResetRegions();}
            if(k.Keycode==Key.P){physics=!physics;ResetRegions();}
            if(k.Keycode==Key.Tab){play=!play;clipTime=0;}
            if(k.Keycode==Key.R){Sample(poseIndex);ResetRegions();}
        }
    }
    private async Task Capture(string path)
    {
        await ToSignal(RenderingServer.Singleton,RenderingServer.SignalName.FramePostDraw);
        using var image=GetViewport().GetTexture().GetImage();System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);Require(image.SavePng(path)==Error.Ok,"Screenshot save failed.");
    }
    private async Task Validate(string[] args)
    {
        string? reportPath=args.FirstOrDefault(s=>s.StartsWith("--report=",StringComparison.Ordinal))?[9..];
        string? capture=args.FirstOrDefault(s=>s.StartsWith("--capture-dir=",StringComparison.Ordinal))?[14..];
        Require(capture==null||DisplayServer.GetName()!="headless","Captures require rendered execution.");
        Sample(0);var neutralRotations=Enumerable.Range(0,rig.GetBoneCount()).Select(rig.GetBonePoseRotation).ToArray();
        var poseResults=new List<object>();
        foreach(int i in new[]{0,1,2,3,4,5,6,7})
        {
            poseIndex=i;Sample(i);ResetRegions();UpdateVisual();
            int joint=rig.FindBone(i==1?"UpperArm.L":i==2||i==3||i==5?"Thigh.L":i==4?"Chest":i==6?"Root":"Head");
            float angle=neutralRotations[joint].AngleTo(rig.GetBonePoseRotation(joint));
            if(i is >0 and <7)Require(angle>.12f,$"Pose {i} did not animate the expected joint relative to neutral.");
            foreach(var s in surfaces)Require(s.MaxDisplacement<.001f,"Reset support applied double displacement.");
            poseResults.Add(new {pose=PoseNames[i],bone=rig.GetBoneName(joint),angleRelativeToNeutralRadians=angle});
            if(capture!=null)await Capture(System.IO.Path.Combine(capture,$"pose-{i}.png"));
        }
        poseIndex=0;Sample(0);ResetRegions();
        double[] peakVolume=new double[regions.Length];float peakSurface=0;int inverted=0;
        for(int tick=0;tick<240;tick++)
        {
            if(tick==60)jumpTime=0;Step(1.0/60);
            for(int r=0;r<regions.Length;r++)
            {
                var d=regions[r].Body.Inspect();Require(d.Finite,"Nonfinite character tissue state.");inverted+=d.InvertedElements;peakVolume[r]=Math.Max(peakVolume[r],d.MaxVolumeError);
            }
            if(tick%4==0||tick==239)
            {
                UpdateVisual();peakSurface=Math.Max(peakSurface,surfaces.Max(s=>s.MaxDisplacement));
                if(capture!=null)await Capture(System.IO.Path.Combine(capture,"motion",$"frame-{tick/4:0000}.png"));
            }
        }
        Require(inverted==0,"Character jump inverted tetrahedra.");Require(peakSurface>.0001f,"Simulation never reached the visible body.");
        physics=false;UpdateVisual();Require(surfaces.All(s=>s.Source.Visible&&!s.Display.Visible),"Physics-disabled skinned fallback failed.");
        var bodySurface=surfaces.Single(s=>s.Source.Name.ToString()=="Body");
        Require(CharacterMaterials.HasLinearColorPolicy(bodySurface.Source.GetActiveMaterial(0)),"Body linear vertex-colour shader policy was lost.");
        if(capture!=null)await Capture(System.IO.Path.Combine(capture,"fallback.png"));
        var report=new {passed=true,sourceCommit=System.Environment.GetEnvironmentVariable("GITHUB_SHA"),engine=Engine.GetVersionInfo()["string"].AsString(),headless=DisplayServer.GetName()=="headless",boneCount=rig.GetBoneCount(),boundSurfaceVertices=surfaces.Sum(s=>s.BoundVertices),maxRestSkinErrorM=surfaces.Max(s=>s.RestSkinError),poseSamples=poseResults,regions=regions.Select((r,i)=>new{name=r.Definition.Name,peakLocalVolumeChange=peakVolume[i],final=r.Body.Inspect(),provisionalFivePercentTarget=peakVolume[i]<=.05}),peakSurfaceDisplacementM=peakSurface,invertedElements=inverted,fallbackVerified=true,linearVertexColorPolicyVerified=true,limitations="Early character prototype. Pose import and isolated jump integrity checked; collision realism, skinning quality, likeness, cloth restraint, and target-PC performance are not certified."};
        string json=JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true});GD.Print(json);if(reportPath!=null)System.IO.File.WriteAllText(reportPath,json);
        GD.Print("YOKAI_CHARACTER_RUNTIME_PASS");GetTree().Quit();
    }
    private void BuildStage()
    {
        AddChild(new WorldEnvironment{Environment=new Godot.Environment{BackgroundMode=Godot.Environment.BGMode.Color,BackgroundColor=new(.08f,.09f,.12f),AmbientLightSource=Godot.Environment.AmbientSource.Color,AmbientLightColor=Colors.White,AmbientLightEnergy=.6f}});
        AddChild(new DirectionalLight3D{RotationDegrees=new(-38,-28,0),LightEnergy=1.0f});
        AddChild(new DirectionalLight3D{RotationDegrees=new(-15,135,0),LightEnergy=.6f});
        AddChild(new MeshInstance3D{Mesh=new PlaneMesh{Size=new(20,20)},MaterialOverride=new StandardMaterial3D{AlbedoColor=new(.16f,.18f,.22f),Roughness=1}});
        camera=new Camera3D{Current=true,Fov=38};AddChild(camera);MoveCamera();
        var canvas=new CanvasLayer();AddChild(canvas);label=new Label{Position=new(20,18)};label.AddThemeFontSizeOverride("font_size",16);canvas.AddChild(label);
    }
    private void MoveCamera(){camera.Position=new Vector3(MathF.Sin(yaw)*distance,1.1f+MathF.Sin(pitch)*distance,MathF.Cos(yaw)*distance);camera.LookAt(new Vector3(0,1.08f,0));}
}