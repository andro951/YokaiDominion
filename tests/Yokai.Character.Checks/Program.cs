using System.Text.Json;
using Yokai.Tissue;

if(args.Length<1) throw new ArgumentException("Pass the authored tissue-regions.json path.");
var asset=CharacterTissueAsset.Parse(File.ReadAllText(args[0]));
var checks=new List<object>();
void Require(bool condition,string message) {if(!condition) throw new InvalidOperationException(message);}
Require(asset.Regions.Length==4,"Expected the four authored character regions.");
foreach(var def in asset.Regions)
{
    var region=def.CreateRuntime(); var mesh=region.Body.Mesh;
    Require(mesh.VertexCount==125&&mesh.ElementCount==384,"Unexpected cage topology.");
    V3 center=RegionDefinition.Vector(def.Center),radius=RegionDefinition.Vector(def.Radii);
    V3 point=center+new V3(0,0,def.OutwardZ*radius.Z*.65);
    var map=region.Bind(new[]{point,new V3(100,100,100)});
    Require(map.Vertices.Length==1,"Binding must include interior sample and reject remote point.");
    V3[] deltas=new V3[2]; double[] weights=new double[2];
    map.Accumulate(region,deltas,weights); Require(deltas[0].Length<1e-10,"Rest embedding creates a spurious displacement.");
    RigidPose pose=RigidPose.AroundPivot(Q4.FromAxisAngle(V3.UnitY,.35),center,new V3(.1,.2,.1));
    region.Body.ResetPose(pose); Array.Clear(deltas); Array.Clear(weights); map.Accumulate(region,deltas,weights);
    Require(deltas[0].Length<1e-9,"Rigid motion must not be applied twice to the surface.");
    region.Body.Reset(); double peak=0; double motion=0;
    for(int tick=0;tick<240;tick++)
    {
        double time=tick/60.0,phase=(time-1)/.9;
        double jump=phase>0&&phase<1?.30*4*phase*(1-phase):0;
        var anchor=RigidPose.FromTranslation(new V3(0,jump,0)); region.Body.Step(1.0/60,anchor);
        var d=region.Body.Inspect(); Require(d.Finite&&d.InvertedElements==0,$"{def.Name}: nonfinite or inverted tissue."); peak=Math.Max(peak,d.MaxVolumeError);
        foreach(var a in def.Attachments.Where(a=>a.Compliance==0)) Require((region.Body.Positions[a.Vertex]-anchor.TransformPoint(mesh.RestPositions[a.Vertex])).Length<1e-8,"Kinematic attachment drift.");
        Array.Clear(deltas); Array.Clear(weights); map.Accumulate(region,deltas,weights); motion=Math.Max(motion,deltas[0].Length);
    }
    Require(motion>1e-5,"No actual dynamic displacement measured.");
    checks.Add(new {region=def.Name,vertices=mesh.VertexCount,elements=mesh.ElementCount,attachments=def.Attachments.Length,restVolumeM3=mesh.RestVolume,peakLocalVolumeChange=peak,finalDiagnostics=region.Body.Inspect(),maxSampleDisplacementM=motion,integrityPassed=true,provisionalFivePercentVolumeTarget=peak<=.05});
}
try {CharacterTissueAsset.Parse("{\"schemaVersion\":99}");throw new InvalidOperationException("Bad schema accepted.");} catch(ArgumentException) {}
string report=JsonSerializer.Serialize(new {sourceCommit=Environment.GetEnvironmentVariable("GITHUB_SHA"),runtime=Environment.Version.ToString(),integrityPassed=true,regions=checks,limitations="Numerical integrity on four authored cages only. No claim of anatomical realism, full-pose contact, or GPU performance."},new JsonSerializerOptions{WriteIndented=true});
Console.WriteLine(report);
string output=args.Length>1?args[1]:"character-numerical.json"; Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output))!); File.WriteAllText(output,report);
Console.WriteLine("YOKAI_CHARACTER_NUMERICAL_PASS");
