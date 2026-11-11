using System.Text.Json;
using Yokai.Tissue;

var results=new List<object>(); int failed=0;
void Check(string name,Action test)
{
    try { test(); Console.WriteLine($"PASS {name}"); results.Add(new { name,passed=true,error=(string?)null }); }
    catch(Exception e) { failed++; Console.WriteLine($"FAIL {name}: {e.Message}"); results.Add(new { name,passed=false,error=e.ToString() }); }
}
void Require(bool ok,string message="Assertion failed") { if(!ok) throw new InvalidOperationException(message); }
void Near(double actual,double expected,double tolerance,string name="value")=>Require(Math.Abs(actual-expected)<=tolerance,$"{name}: {actual:G17}, expected {expected:G17} +/- {tolerance:G3}");
void Reject(Action action) { bool rejected=false; try {action();} catch(ArgumentException) {rejected=true;} Require(rejected,"Invalid input was accepted"); }
TetMesh UnitTet()=>new([V3.Zero,V3.UnitX,V3.UnitY,V3.UnitZ],[new(0,1,2,3)]);
TetMesh SmallBlock()=>TetMesh.Block(2,2,2,new(0.2,0.2,0.2),new(-0.1,0.5,-0.1));
TissueBody Make(TetMesh? mesh=null,SolverSettings? settings=null)=>new(mesh??SmallBlock(),new TissueMaterial(),settings??new SolverSettings());

Check("signed volume and inverted orientation normalization",()=>{
    Near(Tetrahedron.SignedVolume(V3.Zero,V3.UnitX,V3.UnitY,V3.UnitZ),1.0/6,1e-15);
    var m=new TetMesh([V3.Zero,V3.UnitX,V3.UnitY,V3.UnitZ],[new(0,2,1,3)]);
    Require(m.Elements[0].Volume(m.RestPositions)>0);
});
Check("matrix inverse and column convention",()=>{
    M3 m=new(new(2,0.2,0.1),new(-0.3,3,0.4),new(0.2,0.1,4));
    Near((m*m.Inverse()-M3.Identity).NormSquared,0,1e-24);
});
Check("mesh volume, boundary and total density-derived mass",()=>{
    var m=SmallBlock(); var b=Make(m);
    Near(m.RestVolume,0.008,1e-14); Near(b.Masses.ToArray().Sum(),8,1e-11);
    Require(m.Boundary.Length==48,$"boundary triangles: {m.Boundary.Length}");
});
Check("invalid/degenerate/duplicate mesh rejection",()=>{
    Reject(()=>new TetMesh([V3.Zero,V3.UnitX,V3.UnitY,V3.UnitX],[new(0,1,2,3)]));
    Reject(()=>new TetMesh([V3.Zero,V3.UnitX,V3.UnitY,V3.UnitZ],[new(0,1,2,4)]));
    Reject(()=>new TetMesh([V3.Zero,V3.UnitX,V3.UnitY,V3.UnitZ],[new(0,1,2,3),new(3,2,1,0)]));
    Reject(()=>new TetMesh([new(double.NaN,0,0),V3.UnitX,V3.UnitY,V3.UnitZ],[new(0,1,2,3)]));
});
Check("material parameter rejection",()=>{
    Reject(()=>new TissueMaterial(-1)); Reject(()=>new TissueMaterial(poissonRatio:0.5));
    Reject(()=>new TissueMaterial(density:0)); Reject(()=>new TissueMaterial(double.NaN));
});
Check("rest energy and stress are zero",()=>{
    var m=new TissueMaterial(); Near(NeoHookean.EnergyDensity(M3.Identity,m),0,1e-10);
    Near(NeoHookean.FirstPiola(M3.Identity,m).NormSquared,0,1e-16);
});
Check("energy gradient matches central differences",()=>{
    var m=new TissueMaterial(); M3 f=new(new(1.08,0.04,-0.03),new(0.06,0.95,0.02),new(0.02,-0.01,1.02));
    M3 p=NeoHookean.FirstPiola(f,m); const double eps=1e-6;
    for(int c=0;c<3;c++) for(int r=0;r<3;r++)
    {
        M3 Change(double h) { V3[] cols=[f.C0,f.C1,f.C2]; cols[c]=cols[c].With(r,cols[c][r]+h); return new(cols[0],cols[1],cols[2]); }
        double fd=(NeoHookean.EnergyDensity(Change(eps),m)-NeoHookean.EnergyDensity(Change(-eps),m))/(2*eps);
        Near(fd,p[c][r],2e-4,$"stress [{r},{c}]");
    }
});
Check("energy is rigid-rotation invariant",()=>{
    var m=new TissueMaterial(); M3 f=new(new(1.1,0.1,0),new(0,0.9,0),new(0,0.02,1));
    Near(NeoHookean.EnergyDensity(M3.RotationY(0.73)*f,m),NeoHookean.EnergyDensity(f,m),1e-9);
});
Check("coupled elasticity remains at unloaded rest",()=>{
    var b=Make(settings:new SolverSettings {Gravity=V3.Zero,VelocityDrag=0});
    for(int i=0;i<240;i++) b.Step(1.0/120);
    double error=0; for(int i=0;i<b.Mesh.VertexCount;i++) error=Math.Max(error,(b.Positions[i]-b.Mesh.RestPositions[i]).Length);
    Near(error,0,1e-8,"rest drift"); Require(b.Inspect().InvertedElements==0);
});
Check("free fall preserves rest shape",()=>{
    var b=Make(settings:new SolverSettings {VelocityDrag=0});
    for(int i=0;i<30;i++) b.Step(1.0/120);
    V3 delta=b.Positions[0]-b.Mesh.RestPositions[0]; Require(delta.Y<-0.25);
    for(int i=1;i<b.Mesh.VertexCount;i++) Near((b.Positions[i]-b.Mesh.RestPositions[i]-delta).Length,0,1e-8);
});
Check("pinned boundary follows moving support exactly",()=>{
    var b=Make(); for(int i=0;i<b.Mesh.VertexCount;i++) if(b.Mesh.RestPositions[i].Y>0.699) b.Attach(i);
    for(int i=0;i<120;i++) b.Step(1.0/120,new(0.01*Math.Sin(i/30.0),0,0));
    for(int i=0;i<b.Mesh.VertexCount;i++) if(b.Mesh.RestPositions[i].Y>0.699)
        Near((b.Positions[i]-b.Mesh.RestPositions[i]-b.AnchorOffset).Length,0,1e-12);
    var d=b.Inspect(); Require(d.Finite&&d.InvertedElements==0); Require(d.MaxVolumeError<0.08,$"volume error {d.MaxVolumeError}");
});
Check("soft attachment transmits support without NaNs",()=>{
    var b=Make(); for(int i=0;i<b.Mesh.VertexCount;i++) if(b.Mesh.RestPositions[i].Y>0.699) b.Attach(i,1e-5);
    for(int i=0;i<120;i++) b.Step(1.0/120,new(0,0.02,0));
    Require(b.Inspect().Finite&&b.Inspect().InvertedElements==0);
});
Check("floor drop produces finite nonpenetrating contact",()=>{
    var b=Make(); b.Contacts.Add(new ContactPlane(V3.UnitY,0));
    for(int i=0;i<240;i++) b.Step(1.0/120);
    foreach(V3 p in b.Positions) Require(p.Y>=b.Settings.ParticleRadius-1e-9,$"floor penetration {p.Y}");
    var d=b.Inspect(); Require(d.Finite&&d.InvertedElements==0,$"drop diagnostics {d}");
});
Check("capsule signed distance including axis case",()=>{
    var c=new ContactCapsule(new(0,0,0),new(0,1,0),0.2);
    Near(c.Distance(new(0.5,0.5,0),out V3 n),0.3,1e-12); Near((n-V3.UnitX).Length,0,1e-12);
    Near(c.Distance(new(0,0.5,0),out n),-0.2,1e-12); Near(n.Length,1,1e-12); Near(V3.Dot(n,V3.UnitY),0,1e-12);
});
Check("barycentric embedding reproduces affine deformation",()=>{
    var mesh=UnitTet(); V3[] p=[new(0.1,0.2,0.3),new(0.2,0.3,0.1)]; var bind=SurfaceBinding.Create(mesh,p);
    M3 a=new(new(1.2,0,0),new(0.1,0.8,0),new(0.2,0,1)); V3 t=new(2,3,4);
    V3[] transformed=mesh.RestPositions.ToArray().Select(v=>a*v+t).ToArray(),dst=new V3[p.Length];
    bind.Evaluate(mesh,transformed,dst);
    for(int i=0;i<p.Length;i++) Near((dst[i]-(a*p[i]+t)).Length,0,1e-12);
    Reject(()=>SurfaceBinding.Create(mesh,[new(3,3,3)]));
});
Check("teleport preserves deformation and velocity",()=>{
    var b=Make(); b.Step(1.0/120); var before=b.Positions.ToArray(); var velocities=b.Velocities.ToArray(); V3 delta=new(10,0,-3); b.Translate(delta);
    for(int i=0;i<before.Length;i++) { Near((b.Positions[i]-before[i]-delta).Length,0,1e-12); Near((b.Velocities[i]-velocities[i]).Length,0,1e-12); }
});
Check("reset restores rest shape",()=>{
    var b=Make(); b.Step(1.0/120); b.Reset();
    for(int i=0;i<b.Mesh.VertexCount;i++) { Near((b.Positions[i]-b.Mesh.RestPositions[i]).Length,0,0); Near(b.Velocities[i].Length,0,0); }
});
Check("invalid timesteps and duplicate attachments rejected",()=>{
    var b=Make(); Reject(()=>b.Step(0)); Reject(()=>b.Step(double.NaN)); Reject(()=>b.Step(0.1)); b.Attach(0); Reject(()=>b.Attach(0));
});

Directory.CreateDirectory("artifacts");
File.WriteAllText("artifacts/core-results.json",JsonSerializer.Serialize(new { schemaVersion=1,utc=DateTime.UtcNow,revision=Environment.GetEnvironmentVariable("GITHUB_SHA")??"local",runtime=System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription,os=System.Runtime.InteropServices.RuntimeInformation.OSDescription,total=results.Count,failed,results },new JsonSerializerOptions {WriteIndented=true}));
Console.WriteLine($"{results.Count-failed}/{results.Count} checks passed. Numerical checks do not establish anatomical realism or game readiness.");
return failed==0 ? 0:1;
