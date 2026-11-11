using System.Text.Json;

namespace Yokai.Tissue;

/// <summary>Engine-neutral, versioned authoring interchange. Coordinates: glTF Y-up, metres.</summary>
public sealed class CharacterTissueAsset
{
    public int SchemaVersion { get; set; }
    public string CoordinateSystem { get; set; } = "";
    public RegionDefinition[] Regions { get; set; } = [];
    public static CharacterTissueAsset Parse(string json)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(json);
        var asset=JsonSerializer.Deserialize<CharacterTissueAsset>(json,new JsonSerializerOptions {PropertyNameCaseInsensitive=true}) ?? throw new ArgumentException("Empty tissue asset.");
        if(asset.SchemaVersion!=1 || !asset.CoordinateSystem.StartsWith("glTF Y-up",StringComparison.Ordinal)) throw new ArgumentException("Unsupported schema or coordinate convention.");
        if(asset.Regions.Length==0 || asset.Regions.Select(r=>r.Name).Distinct().Count()!=asset.Regions.Length) throw new ArgumentException("Missing or duplicate regions.");
        foreach(var region in asset.Regions) region.Validate();
        return asset;
    }
}
public sealed class AttachmentDefinition
{
    public int Vertex { get; set; }
    public double Compliance { get; set; }
}
public sealed class RegionDefinition
{
    public string Name { get; set; }="";
    public string Bone { get; set; }="";
    public double[] Center { get; set; }=[];
    public double[] Radii { get; set; }=[];
    public double OutwardZ { get; set; }
    public double[][] Nodes { get; set; }=[];
    public int[][] Tetrahedra { get; set; }=[];
    public AttachmentDefinition[] Attachments { get; set; }=[];
    public double YoungModulus { get; set; }
    public double PoissonRatio { get; set; }
    public double Density { get; set; }
    public int SolverSubsteps { get; set; }=8;
    public int SolverIterations { get; set; }=8;
    public double VelocityDrag { get; set; }=4;
    public SolverSettings CreateSettings()=>new() {Substeps=SolverSubsteps,Iterations=SolverIterations,VelocityDrag=VelocityDrag,ParticleRadius=.003};
    public static V3 Vector(double[] a)
    {
        if(a.Length!=3 || a.Any(x=>!double.IsFinite(x))) throw new ArgumentException("Expected a finite 3-vector.");
        return new(a[0],a[1],a[2]);
    }
    public void Validate()
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(Name); ArgumentException.ThrowIfNullOrWhiteSpace(Bone);
        _=Vector(Center); var r=Vector(Radii);
        if(r.X<=0||r.Y<=0||r.Z<=0||Math.Abs(OutwardZ)!=1) throw new ArgumentException("Invalid region envelope.");
        _=new TissueMaterial(YoungModulus,PoissonRatio,Density);CreateSettings().Validate();
        _=CreateMesh();
        if(Attachments.Length==0||!Attachments.Any(a=>a.Compliance==0)||Attachments.Select(a=>a.Vertex).Distinct().Count()!=Attachments.Length) throw new ArgumentException("Region needs unique attachments and a kinematic support.");
        foreach(var a in Attachments) if(a.Vertex<0||a.Vertex>=Nodes.Length||!double.IsFinite(a.Compliance)||a.Compliance<0) throw new ArgumentException("Invalid attachment.");
    }
    public TetMesh CreateMesh()=>new(Nodes.Select(Vector),Tetrahedra.Select(t=>t.Length==4?new Tetrahedron(t[0],t[1],t[2],t[3]):throw new ArgumentException("Expected four tetrahedron indices.")));
    public CharacterTissueRegion CreateRuntime()=>new(this);
}

/// <summary>Volumetric prototype, graded supports, one bone delta per region; material values are not biological measurements.</summary>
public sealed class CharacterTissueRegion
{
    public RegionDefinition Definition { get; }
    public TissueBody Body { get; }
    public CharacterTissueRegion(RegionDefinition definition)
    {
        definition.Validate(); Definition=definition;
        Body=new(definition.CreateMesh(),new TissueMaterial(definition.YoungModulus,definition.PoissonRatio,definition.Density),definition.CreateSettings());
        foreach(var a in definition.Attachments) Body.Attach(a.Vertex,a.Compliance);
        Body.Contacts.Add(new ContactPlane(V3.UnitY,0));
    }
    public TissueSurfaceMap Bind(IReadOnlyList<V3> restSurface)=>TissueSurfaceMap.Create(this,restSurface);
}

public readonly record struct RegionalVertex(int SurfaceIndex,BoundVertex Embedding,V3 Rest,double Weight);

/// <summary>Barycentric displacement over already-skinned vertices. Zero delta preserves base animation; no outside extrapolation.</summary>
public sealed class TissueSurfaceMap
{
    private readonly RegionalVertex[] vertices;
    public ReadOnlySpan<RegionalVertex> Vertices=>vertices;
    public int RejectedInsideEnvelope { get; }
    private TissueSurfaceMap(RegionalVertex[] vertices,int rejected) {this.vertices=vertices; RejectedInsideEnvelope=rejected;}
    public static TissueSurfaceMap Create(CharacterTissueRegion region,IReadOnlyList<V3> surface)
    {
        var definition=region.Definition; var mesh=region.Body.Mesh;
        V3 center=RegionDefinition.Vector(definition.Center),radius=RegionDefinition.Vector(definition.Radii);
        var inverse=new M3[mesh.ElementCount];
        for(int e=0;e<inverse.Length;e++) inverse[e]=mesh.Elements[e].EdgeMatrix(mesh.RestPositions).Inverse();
        var bound=new List<RegionalVertex>(); int rejected=0;
        for(int i=0;i<surface.Count;i++)
        {
            V3 p=surface[i]; if(!p.IsFinite) throw new ArgumentException("Nonfinite surface point.");
            V3 q=new((p.X-center.X)/radius.X,(p.Y-center.Y)/radius.Y,(p.Z-center.Z)/radius.Z);
            if(q.LengthSquared>1.00001) continue;
            double outward=q.Z*definition.OutwardZ;
            double weight=Smooth((outward+.12)/.60)*Smooth((1-Math.Sqrt(q.X*q.X+q.Y*q.Y))/.25);
            if(weight<1e-5) continue;
            bool found=false;
            for(int e=0;e<mesh.ElementCount;e++)
            {
                var t=mesh.Elements[e]; V3 b=inverse[e]*(p-mesh.RestPositions[t.A]); double a=1-b.X-b.Y-b.Z;
                if(a>=-1e-6&&b.X>=-1e-6&&b.Y>=-1e-6&&b.Z>=-1e-6)
                {bound.Add(new(i,new BoundVertex(e,a,b.X,b.Y,b.Z),p,weight));found=true;break;}
            }
            if(!found) rejected++;
        }
        return new(bound.ToArray(),rejected);
    }
    private static double Smooth(double t) {t=Math.Clamp(t,0,1);return t*t*(3-2*t);}
    public void Accumulate(CharacterTissueRegion region,Span<V3> displacements,Span<double> weights)
    {
        if(displacements.Length!=weights.Length) throw new ArgumentException("Surface buffer mismatch.");
        var mesh=region.Body.Mesh; var x=region.Body.Positions; var pose=region.Body.AnchorPose;
        foreach(var v in vertices)
        {
            if(v.SurfaceIndex>=displacements.Length) throw new ArgumentException("Surface buffer too small.");
            var b=v.Embedding; var t=mesh.Elements[b.Element];
            V3 actual=x[t.A]*b.A+x[t.B]*b.B+x[t.C]*b.C+x[t.D]*b.D;
            V3 delta=actual-pose.TransformPoint(v.Rest);
            displacements[v.SurfaceIndex]+=delta*v.Weight; weights[v.SurfaceIndex]+=v.Weight;
        }
    }
    public static V3 NormalizeAccumulated(V3 displacement,double weight)=>displacement/Math.Max(1,weight);
}
