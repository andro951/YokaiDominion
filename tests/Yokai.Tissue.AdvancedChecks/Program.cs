using System.Text.Json;
using Yokai.Tissue;

var results=new List<object>(); int failed=0;
void Require(bool ok,string message="Assertion failed") {if(!ok) throw new InvalidOperationException(message);}
void Near(double value,double expected,double tolerance)=>Require(Math.Abs(value-expected)<=tolerance,$"{value:G17} != {expected:G17}, tolerance {tolerance:G3}");
void Check(string name,Action action)
{
    try {action(); Console.WriteLine($"PASS {name}"); results.Add(new {name,passed=true,error=(string?)null});}
    catch(Exception e) {failed++; Console.WriteLine($"FAIL {name}: {e}"); results.Add(new {name,passed=false,error=e.ToString()});}
}
void Reject(Action action) {bool caught=false;try {action();} catch(ArgumentException) {caught=true;}Require(caught,"Invalid input accepted");}
TetMesh Small()=>TetMesh.Block(2,2,2,new(0.2,0.2,0.2),new(-0.1,0.5,-0.1));
Check("quaternion convention and inverse",()=>{
    var q=Q4.FromAxisAngle(V3.UnitY,0.75); V3 p=new(0.2,0.3,0.4);
    Near((q.Rotate(p)-M3.RotationY(0.75)*p).Length,0,1e-14);
    Near((q.Inverse.Rotate(q.Rotate(p))-p).Length,0,1e-14);
});
Check("shortest path handles antipodal quaternion",()=>{
    var q=Q4.FromAxisAngle(V3.UnitZ,0.8); var minus=new Q4(-q.X,-q.Y,-q.Z,-q.W);
    Near((Q4.Slerp(q,minus,0.5).Rotate(V3.UnitX)-q.Rotate(V3.UnitX)).Length,0,1e-14);
});
Check("pose composition and bind inverse",()=>{
    var bind=new RigidPose(new(1,2,3),Q4.FromAxisAngle(V3.UnitY,0.3));
    var animated=new RigidPose(new(2,2.3,3),Q4.FromAxisAngle(V3.UnitZ,0.5));
    var delta=animated*bind.Inverse; V3 local=new(0.1,0.2,0.3);
    Near((delta.TransformPoint(bind.TransformPoint(local))-animated.TransformPoint(local)).Length,0,1e-13);
});
Check("pivot rotation keeps attachment centre fixed",()=>{
    V3 pivot=new(0,1.3,0),shift=new(0.1,0,0);
    var pose=RigidPose.AroundPivot(Q4.FromAxisAngle(V3.UnitZ,1.2),pivot,shift);
    Near((pose.TransformPoint(pivot)-pivot-shift).Length,0,1e-14);
});
Check("rotated unloaded rest has no artificial deformation",()=>{
    var b=new TissueBody(Small(),new TissueMaterial(),new SolverSettings {Gravity=V3.Zero,VelocityDrag=0});
    var pose=new RigidPose(new(2,-1,3),Q4.FromAxisAngle(new(1,2,3),1.1)); b.ResetPose(pose);
    for(int i=0;i<120;i++) b.Step(1.0/120);
    for(int i=0;i<b.Mesh.VertexCount;i++) Near((b.Positions[i]-pose.TransformPoint(b.Mesh.RestPositions[i])).Length,0,1e-8);
});
Check("turning support preserves hard attachment and finite tissue",()=>{
    var b=new TissueBody(Small(),new TissueMaterial(8000,0.499));
    for(int i=0;i<b.Mesh.VertexCount;i++) if(b.Mesh.RestPositions[i].Y>0.699) b.Attach(i);
    for(int frame=0;frame<240;frame++)
    {
        var pose=RigidPose.AroundPivot(Q4.FromAxisAngle(V3.UnitZ,0.5*Math.Sin(frame/90.0)),new(0,0.7,0));
        b.Step(1.0/120,pose);
        for(int i=0;i<b.Mesh.VertexCount;i++) if(b.Mesh.RestPositions[i].Y>0.699) Near((b.Positions[i]-pose.TransformPoint(b.Mesh.RestPositions[i])).Length,0,1e-12);
        var d=b.Inspect(); Require(d.Finite&&d.InvertedElements==0); Require(d.MaxVolumeError<0.08,$"rotation volume error {d.MaxVolumeError}");
    }
});
Check("rigid teleport rotates velocity without impulse",()=>{
    var b=new TissueBody(Small(),new TissueMaterial()); b.Step(1.0/120);
    var x=b.Positions.ToArray(); var v=b.Velocities.ToArray();
    var delta=new RigidPose(new(5,2,-3),Q4.FromAxisAngle(V3.UnitZ,0.7)); b.Teleport(delta);
    for(int i=0;i<x.Length;i++) {Near((b.Positions[i]-delta.TransformPoint(x[i])).Length,0,1e-12);Near((b.Velocities[i]-delta.Rotation.Rotate(v[i])).Length,0,1e-12);}
});
Check("invalid rotations and poses rejected",()=>{
    Reject(()=>new Q4(0,0,0,0)); Reject(()=>Q4.FromAxisAngle(V3.Zero,1)); Reject(()=>Q4.Slerp(Q4.Identity,Q4.Identity,double.NaN));
    var b=new TissueBody(Small(),new TissueMaterial()); Reject(()=>b.Step(1.0/120,default(RigidPose))); Reject(()=>b.Teleport(default));
});
Check("jump fixture retains volume within explicit baseline limits",()=>{
    var mesh=TetMesh.Block(3,3,3,new(0.5,0.3,0.35),new(-0.25,1,-0.175));
    var b=new TissueBody(mesh,new TissueMaterial(6500,0.499),new SolverSettings {Substeps=4,Iterations=5,VelocityDrag=1});
    for(int i=0;i<mesh.VertexCount;i++) if(mesh.RestPositions[i].Y>1.299) b.Attach(i);
    b.Contacts.Add(new ContactPlane(V3.UnitY,0)); double peak=0;
    for(int frame=0;frame<600;frame++)
    {
        double time=(frame+1)/120.0,u=(time-1)/0.75;
        double elevation=u>=0&&u<=1?0.3*Math.Pow(Math.Sin(Math.PI*u),2):0;
        b.Step(1.0/120,new V3(0.025*Math.Sin(time*2),elevation,0));
        var d=b.Inspect(); Require(d.Finite&&d.InvertedElements==0); peak=Math.Max(peak,d.MaxVolumeError);
    }
    Require(peak<0.05,$"peak local volume error {peak:P3} exceeds 5% fixture limit");
    Require(b.Inspect().MaxVolumeError<0.02,"end volume error exceeds 2% fixture limit");
    Console.WriteLine($"  peak={peak:P4}, final={b.Inspect().MaxVolumeError:P4}; this is a fixture envelope, not a biological validation.");
});
Directory.CreateDirectory("artifacts");
File.WriteAllText("artifacts/advanced-results.json",JsonSerializer.Serialize(new {
    schemaVersion=1,utc=DateTime.UtcNow,revision=Environment.GetEnvironmentVariable("YOKAI_SOURCE_REVISION")??Environment.GetEnvironmentVariable("GITHUB_SHA")??"local",
    runtime=System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription,os=System.Runtime.InteropServices.RuntimeInformation.OSDescription,total=results.Count,failed,results
},new JsonSerializerOptions {WriteIndented=true}));
Console.WriteLine($"{results.Count-failed}/{results.Count} advanced checks passed.");
return failed==0?0:1;
