namespace Yokai.Tissue;

public readonly record struct BoundVertex(int Element,double A,double B,double C,double D);

/// <summary>Barycentric volumetric embedding. Rejects outside vertices rather than silently extrapolating.</summary>
public sealed class SurfaceBinding
{
    private readonly BoundVertex[] bindings;
    public ReadOnlySpan<BoundVertex> Vertices=>bindings;
    private SurfaceBinding(BoundVertex[] bindings)=>this.bindings=bindings;
    public static SurfaceBinding Create(TetMesh mesh,IEnumerable<V3> vertices,double tolerance=1e-7)
    {
        if(!double.IsFinite(tolerance)||tolerance<0) throw new ArgumentOutOfRangeException(nameof(tolerance));
        var output=new List<BoundVertex>();
        foreach(V3 p in vertices)
        {
            if(!p.IsFinite) throw new ArgumentException("Non-finite surface vertex.");
            bool found=false;
            for(int e=0;e<mesh.ElementCount;e++)
            {
                var t=mesh.Elements[e];
                V3 b=t.EdgeMatrix(mesh.RestPositions).Inverse()*(p-mesh.RestPositions[t.A]);
                double a=1-b.X-b.Y-b.Z;
                if(a>=-tolerance&&b.X>=-tolerance&&b.Y>=-tolerance&&b.Z>=-tolerance)
                { output.Add(new(e,a,b.X,b.Y,b.Z)); found=true; break; }
            }
            if(!found) throw new ArgumentException($"Surface vertex {output.Count} is outside the simulation volume.");
        }
        return new(output.ToArray());
    }
    public void Evaluate(TetMesh mesh,ReadOnlySpan<V3> simulated,Span<V3> destination)
    {
        if(simulated.Length!=mesh.VertexCount||destination.Length!=bindings.Length) throw new ArgumentException("Binding buffer length mismatch.");
        for(int i=0;i<bindings.Length;i++)
        {
            var b=bindings[i]; var t=mesh.Elements[b.Element];
            destination[i]=simulated[t.A]*b.A+simulated[t.B]*b.B+simulated[t.C]*b.C+simulated[t.D]*b.D;
        }
    }
}
