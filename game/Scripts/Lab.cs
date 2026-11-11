using Godot;
using Yokai.Tissue;

namespace YokaiDominion;

/// <summary>Numerical integration lab, deliberately not a character-quality showcase.</summary>
public partial class Lab : Node3D
{
    private TissueBody body=null!;
    private readonly ArrayMesh surface=new();
    private MeshInstance3D tissueNode=null!,support=null!;
    private Camera3D camera=null!;
    private Label hud=null!;
    private int ticks;
    private double clock,jumpTime=-1,peakVolumeError;
    private bool paused,attached=true,smoke,captureStarted,captureDone,turning;
    private string? capturePath;
    private float yaw=0.65f,pitch=0.3f,distance=2.8f;
    private bool headless;

    public override void _Ready()
    {
        try
        {
            string[] args=OS.GetCmdlineUserArgs(); smoke=args.Contains("--smoke");
            capturePath=args.FirstOrDefault(a=>a.StartsWith("--capture=",StringComparison.Ordinal))?[10..];
            headless=DisplayServer.GetName()=="headless";
            if(headless&&capturePath!=null) throw new InvalidOperationException("A screenshot requires a rendering display, not headless mode.");
            BuildStage(); ResetBody(true); UpdateSurface();
            GD.Print($"YOKAI_LAB_READY Godot={Engine.GetVersionInfo()["string"]} particles={body.Mesh.VertexCount} tetrahedra={body.Mesh.ElementCount}");
        }
        catch(Exception e) { Fail(e); }
    }
    private static Vector3 G(V3 v)=>new((float)v.X,(float)v.Y,(float)v.Z);
    private static Quaternion G(Q4 q)=>new((float)q.X,(float)q.Y,(float)q.Z,(float)q.W);
    private static StandardMaterial3D Material(Color color)=>new() {AlbedoColor=color,Roughness=0.85f,MetallicSpecular=0.2f};
    private void BuildStage()
    {
        AddChild(new WorldEnvironment {Environment=new Godot.Environment {
            BackgroundMode=Godot.Environment.BGMode.Color,BackgroundColor=new(0.035f,0.045f,0.07f),
            AmbientLightSource=Godot.Environment.AmbientSource.Color,AmbientLightColor=new(0.7f,0.78f,0.9f),AmbientLightEnergy=0.45f}});
        AddChild(new DirectionalLight3D {RotationDegrees=new(-45,-30,0),LightEnergy=1.0f,ShadowEnabled=true});
        AddChild(new OmniLight3D {Position=new(-1,2,1),LightEnergy=0.35f,OmniRange=5});
        AddChild(new MeshInstance3D {Mesh=new BoxMesh {Size=new(4,0.06f,4)},Position=new(0,-0.03f,0),MaterialOverride=Material(new(0.14f,0.18f,0.22f))});
        support=new MeshInstance3D {Mesh=new BoxMesh {Size=new(0.58f,0.035f,0.43f)},Position=new(0,1.32f,0),MaterialOverride=Material(new(0.23f,0.65f,0.67f))}; AddChild(support);
        tissueNode=new MeshInstance3D {Mesh=surface,MaterialOverride=Material(new(0.53f,0.49f,0.65f))}; AddChild(tissueNode);
        camera=new Camera3D {Current=true,Fov=45}; AddChild(camera); PositionCamera();
        var canvas=new CanvasLayer(); AddChild(canvas);
        canvas.AddChild(new ColorRect {Position=new(16,16),Size=new(1010,168),Color=new(0.02f,0.025f,0.04f,0.88f),MouseFilter=Control.MouseFilterEnum.Ignore});
        hud=new Label {Position=new(30,26)}; hud.AddThemeFontSizeOverride("font_size",18); canvas.AddChild(hud);
        var footer=new Label {Text="ENGINE / PHYSICS TEST FIXTURE   -   NOT THE CHARACTER MODEL",Position=new(28,674)};
        footer.AddThemeFontSizeOverride("font_size",16); canvas.AddChild(footer);
    }
    private void ResetBody(bool attach)
    {
        attached=attach; clock=0; jumpTime=-1; peakVolumeError=0; turning=false;
        var mesh=TetMesh.Block(3,3,3,new(0.5,0.3,0.35),new(-0.25,1,-0.175));
        body=new(mesh,new TissueMaterial(6500,0.499),new SolverSettings {Substeps=4,Iterations=5,VelocityDrag=1});
        if(attach) for(int i=0;i<mesh.VertexCount;i++) if(mesh.RestPositions[i].Y>1.299) body.Attach(i);
        body.Contacts.Add(new ContactPlane(V3.UnitY,0)); support.Visible=attach;
    }
    public override void _PhysicsProcess(double delta)
    {
        if(body==null) return;
        try
        {
            if(!paused)
            {
                clock+=delta;
                if(smoke&&clock>1&&clock<1+delta*1.5) jumpTime=0;
                double elevation=0;
                if(jumpTime>=0)
                {
                    jumpTime+=delta; double u=jumpTime/0.75;
                    if(u<1) elevation=0.3*Math.Pow(Math.Sin(Math.PI*u),2); else jumpTime=-1;
                }
                V3 anchor=attached?new(0.025*Math.Sin(clock*2),elevation,0):V3.Zero;
                Q4 rotation=turning?Q4.FromAxisAngle(V3.UnitZ,0.45*Math.Sin(clock*1.5)):Q4.Identity;
                var pose=RigidPose.AroundPivot(rotation,new(0,1.3,0),anchor);
                body.Step(delta,pose); support.Position=G(pose.TransformPoint(new(0,1.32,0))); support.Quaternion=G(rotation);
                ticks++;
            }
            var d=body.Inspect(); peakVolumeError=Math.Max(peakVolumeError,d.MaxVolumeError);
            hud.Text=$"YOKAI DOMINION  /  TISSUE LAB\n{body.Mesh.VertexCount} particles  |  {body.Mesh.ElementCount} tetrahedra  |  120 Hz\nMin volume ratio: {d.MinJacobian:F3}   Max change: {d.MaxVolumeError:P1}   Peak: {peakVolumeError:P1}   Inversions: {d.InvertedElements}\nSpace: jump   T: turn   D: drop   R: reset   P: pause   Right-drag/wheel: camera\n{(paused?"PAUSED":"RUNNING")}  -  anatomical calibration and full contact are not implemented";
            if(!d.Finite||d.InvertedElements>0) throw new InvalidOperationException($"Lab diagnostics failed: {d}");
            if(smoke&&peakVolumeError>=0.05) throw new InvalidOperationException($"Peak local volume change exceeds fixture limit: {peakVolumeError:P3}");
            if(smoke&&ticks>=600&&(capturePath==null||captureDone))
            {
                if(d.MaxVolumeError>=0.02) throw new InvalidOperationException("Final volume change exceeds fixture limit.");
                GD.Print($"YOKAI_GODOT_SMOKE_PASS ticks={ticks} maxVolumeError={d.MaxVolumeError:G6} peakVolumeError={peakVolumeError:G6} minJ={d.MinJacobian:G6}");
                GetTree().Quit();
            }
        }
        catch(Exception e) { Fail(e); }
    }
    public override void _Process(double delta)
    {
        if(body==null) return;
        try
        {
            if(!headless) UpdateSurface();
            if(capturePath!=null&&!captureStarted&&ticks>=480) { captureStarted=true; Capture(); }
        }
        catch(Exception e) { Fail(e); }
    }
    private void UpdateSurface()
    {
        if(headless) return;
        Vector3[] vertices=new Vector3[body.Mesh.VertexCount],normals=new Vector3[body.Mesh.VertexCount];
        for(int i=0;i<vertices.Length;i++) vertices[i]=G(body.Positions[i]);
        int[] indices=new int[body.Mesh.Boundary.Length*3]; int j=0;
        foreach(var f in body.Mesh.Boundary)
        {
            Vector3 n=(vertices[f.B]-vertices[f.A]).Cross(vertices[f.C]-vertices[f.A]);
            normals[f.A]+=n; normals[f.B]+=n; normals[f.C]+=n;
            // Physics faces are outward CCW; Godot front faces are clockwise.
            indices[j++]=f.A; indices[j++]=f.C; indices[j++]=f.B;
        }
        for(int i=0;i<normals.Length;i++) normals[i]=normals[i].LengthSquared()>1e-16f?normals[i].Normalized():Vector3.Up;
        var arrays=new Godot.Collections.Array(); arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex]=vertices; arrays[(int)Mesh.ArrayType.Normal]=normals; arrays[(int)Mesh.ArrayType.Index]=indices;
        surface.ClearSurfaces(); surface.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles,arrays);
        // Full debug-mesh rebuild is intentional here, not the production deformation path.
    }
    private async void Capture()
    {
        try
        {
            await ToSignal(RenderingServer.Singleton,RenderingServer.SignalName.FramePostDraw);
            using var image=GetViewport().GetTexture().GetImage();
            string path=System.IO.Path.GetFullPath(capturePath!);
            System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
            if(image.SavePng(path)!=Error.Ok) throw new InvalidOperationException("Screenshot save failed.");
            GD.Print($"YOKAI_CAPTURE_SAVED {path}"); captureDone=true;
        }
        catch(Exception e) { Fail(e); }
    }
    private void PositionCamera()
    {
        Vector3 target=new(0,0.9f,0);
        camera.Position=target+new Vector3(MathF.Sin(yaw)*MathF.Cos(pitch),MathF.Sin(pitch),MathF.Cos(yaw)*MathF.Cos(pitch))*distance;
        camera.LookAt(target);
    }
    public override void _UnhandledInput(InputEvent input)
    {
        if(smoke) return;
        if(input is InputEventKey {Pressed:true,Echo:false} k)
        {
            switch(k.Keycode)
            {
                case Key.Space: if(attached) jumpTime=0; break;
                case Key.T: if(attached) turning=!turning; break;
                case Key.D: ResetBody(false); break;
                case Key.R: ResetBody(true); break;
                case Key.P: paused=!paused; break;
                case Key.Escape: GetTree().Quit(); break;
            }
        }
        if(input is InputEventMouseMotion m&&(m.ButtonMask&MouseButtonMask.Right)!=0)
        {yaw-=m.Relative.X*0.006f; pitch=Math.Clamp(pitch+m.Relative.Y*0.006f,-0.2f,1.2f); PositionCamera();}
        if(input is InputEventMouseButton {Pressed:true} b)
        {
            if(b.ButtonIndex==MouseButton.WheelUp) distance=Math.Max(1.2f,distance-0.15f);
            if(b.ButtonIndex==MouseButton.WheelDown) distance=Math.Min(6,distance+0.15f);
            PositionCamera();
        }
    }
    private void Fail(Exception e) {GD.PushError(e.ToString()); SetPhysicsProcess(false); SetProcess(false); GetTree().Quit(1);}
}
