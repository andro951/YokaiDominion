namespace Yokai.Tissue;

public readonly record struct Tetrahedron(int A, int B, int C, int D)
{
    public int this[int i] => i switch { 0=>A, 1=>B, 2=>C, 3=>D, _=>throw new ArgumentOutOfRangeException(nameof(i)) };
    public static double SignedVolume(V3 a,V3 b,V3 c,V3 d) => V3.Dot(b-a,V3.Cross(c-a,d-a))/6;
    public double Volume(ReadOnlySpan<V3> p)=>SignedVolume(p[A],p[B],p[C],p[D]);
    public M3 EdgeMatrix(ReadOnlySpan<V3> p)=>new(p[B]-p[A],p[C]-p[A],p[D]-p[A]);
}
public readonly record struct Triangle(int A,int B,int C);

/// <summary>Validated rest mesh. Input data is copied and exposed read-only.</summary>
public sealed class TetMesh
{
    private readonly V3[] points;
    private readonly Tetrahedron[] tets;
    private readonly Triangle[] boundary;
    public ReadOnlySpan<V3> RestPositions => points;
    public ReadOnlySpan<Tetrahedron> Elements => tets;
    public ReadOnlySpan<Triangle> Boundary => boundary;
    public int VertexCount => points.Length;
    public int ElementCount => tets.Length;
    public double RestVolume { get; }

    public TetMesh(IEnumerable<V3> positions, IEnumerable<Tetrahedron> elements)
    {
        ArgumentNullException.ThrowIfNull(positions);
        ArgumentNullException.ThrowIfNull(elements);
        points=positions.ToArray(); tets=elements.ToArray();
        if (points.Length<4 || tets.Length==0 || points.Any(p=>!p.IsFinite))
            throw new ArgumentException("Mesh requires finite vertices and nonempty tetrahedra.");
        var used=new bool[points.Length];
        var unique=new HashSet<(int,int,int,int)>();
        var faces=new Dictionary<(int,int,int),(Triangle Face,int Count)>();
        double total=0;
        for(int e=0;e<tets.Length;e++)
        {
            var t=tets[e]; int[] ids=[t.A,t.B,t.C,t.D];
            if(ids.Any(i=>i<0||i>=points.Length) || ids.Distinct().Count()!=4)
                throw new ArgumentException($"Invalid indices in tetrahedron {e}.");
            Array.Sort(ids);
            if(!unique.Add((ids[0],ids[1],ids[2],ids[3]))) throw new ArgumentException("Duplicate tetrahedron.");
            double v=t.Volume(points);
            if(!double.IsFinite(v)||Math.Abs(v)<1e-12) throw new ArgumentException($"Degenerate tetrahedron {e}.");
            if(v<0) t=t with { B=t.C,C=t.B };
            tets[e]=t; total+=Math.Abs(v);
            foreach(int id in ids) used[id]=true;
            Face(t.A,t.B,t.C,t.D); Face(t.A,t.D,t.B,t.C);
            Face(t.A,t.C,t.D,t.B); Face(t.B,t.D,t.C,t.A);
        }
        if(used.Any(u=>!u)) throw new ArgumentException("Unreferenced mesh vertex.");
        RestVolume=total;
        boundary=faces.Values.Where(f=>f.Count==1).Select(f=>f.Face).ToArray();
        void Face(int a,int b,int c,int opposite)
        {
            if(V3.Dot(V3.Cross(points[b]-points[a],points[c]-points[a]),points[opposite]-points[a])>0)
                (b,c)=(c,b);
            int[] key=[a,b,c]; Array.Sort(key); var k=(key[0],key[1],key[2]);
            if(faces.TryGetValue(k,out var f))
            {
                if(f.Count==2) throw new ArgumentException("Non-manifold tetrahedral face.");
                faces[k]=(f.Face,2);
            }
            else faces[k]=(new(a,b,c),1);
        }
    }

    public static TetMesh Block(int nx,int ny,int nz,V3 size,V3 origin)
    {
        if(nx<1||ny<1||nz<1||nx>64||ny>64||nz>64 || !size.IsFinite || !origin.IsFinite || size.X<=0||size.Y<=0||size.Z<=0)
            throw new ArgumentOutOfRangeException(nameof(size));
        int Id(int x,int y,int z)=>(z*(ny+1)+y)*(nx+1)+x;
        var p=new V3[(nx+1)*(ny+1)*(nz+1)]; var ts=new List<Tetrahedron>();
        for(int z=0;z<=nz;z++) for(int y=0;y<=ny;y++) for(int x=0;x<=nx;x++)
            p[Id(x,y,z)]=origin+new V3(size.X*x/nx,size.Y*y/ny,size.Z*z/nz);
        for(int z=0;z<nz;z++) for(int y=0;y<ny;y++) for(int x=0;x<nx;x++)
        {
            int a=Id(x,y,z),b=Id(x+1,y,z),c=Id(x+1,y+1,z),d=Id(x,y+1,z);
            int e=Id(x,y,z+1),f=Id(x+1,y,z+1),g=Id(x+1,y+1,z+1),h=Id(x,y+1,z+1);
            ts.AddRange([new(a,b,c,g),new(a,c,d,g),new(a,d,h,g),new(a,h,e,g),new(a,e,f,g),new(a,f,b,g)]);
        }
        return new(p,ts);
    }
}
