namespace Yokai.Tissue;

public readonly record struct BodyDiagnostics(double MinJacobian,double MaxVolumeError,int InvertedElements,double KineticEnergy,bool Finite);

/// <summary>
/// Tetrahedral stable Neo-Hookean XPBD baseline. A coupled 2x2 local solve balances
/// deviatoric/volumetric prestress at rest. This is not an anatomical production solver.
/// Contacts are discrete particle-vs-analytic-shape projections, with no self-collision/CCD.
/// </summary>
public sealed class TissueBody
{
    private readonly V3[] x,v,previous,freeVelocity,contactNormal;
    private readonly double[] mass,invMass;
    private readonly Element[] elements;
    private readonly List<Attachment> attachments=[];
    private readonly TissueMaterial material;
    private V3 anchorOffset;
    public TetMesh Mesh { get; }
    public SolverSettings Settings { get; }
    public List<IContactShape> Contacts { get; }=[];
    public ReadOnlySpan<V3> Positions=>x;
    public ReadOnlySpan<V3> Velocities=>v;
    public ReadOnlySpan<double> Masses=>mass;
    public V3 AnchorOffset=>anchorOffset;

    private sealed class Element(Tetrahedron indices,M3 inverse,double volume)
    {
        public readonly Tetrahedron Ids=indices;
        public readonly M3 Inverse=inverse;
        public readonly double Volume=volume;
        public double LambdaD,LambdaV;
    }
    private sealed class Attachment(int index,double compliance)
    {
        public readonly int Index=index;
        public readonly double Compliance=compliance;
        public V3 Lambda;
    }
    public TissueBody(TetMesh mesh,TissueMaterial material,SolverSettings? settings=null)
    {
        ArgumentNullException.ThrowIfNull(mesh); ArgumentNullException.ThrowIfNull(material);
        Mesh=mesh; this.material=material; Settings=settings??new(); Settings.Validate();
        x=mesh.RestPositions.ToArray(); int n=x.Length;
        v=new V3[n]; previous=new V3[n]; freeVelocity=new V3[n]; contactNormal=new V3[n];
        mass=new double[n]; invMass=new double[n]; elements=new Element[mesh.ElementCount];
        for(int i=0;i<elements.Length;i++)
        {
            var t=mesh.Elements[i]; double volume=t.Volume(x);
            elements[i]=new(t,t.EdgeMatrix(x).Inverse(),volume);
            for(int j=0;j<4;j++) mass[t[j]]+=volume*material.Density/4;
        }
        for(int i=0;i<n;i++) invMass[i]=1/mass[i];
    }

    /// <summary>Zero compliance is kinematic. Positive compliance is a compliant attachment (m/N).</summary>
    public void Attach(int vertex,double compliance=0)
    {
        if(vertex<0||vertex>=x.Length) throw new ArgumentOutOfRangeException(nameof(vertex));
        if(!double.IsFinite(compliance)||compliance<0) throw new ArgumentOutOfRangeException(nameof(compliance));
        if(attachments.Any(a=>a.Index==vertex)) throw new ArgumentException("Vertex already attached.");
        attachments.Add(new(vertex,compliance));
        if(compliance==0) invMass[vertex]=0;
    }
    public void SetParticleState(int vertex,V3 position,V3 velocity)
    {
        if(vertex<0||vertex>=x.Length||!position.IsFinite||!velocity.IsFinite) throw new ArgumentException("Invalid particle state.");
        x[vertex]=position; v[vertex]=velocity;
    }
    public void Reset(V3 offset=default)
    {
        if(!offset.IsFinite) throw new ArgumentException("Non-finite reset offset.");
        for(int i=0;i<x.Length;i++) { x[i]=Mesh.RestPositions[i]+offset; v[i]=default; }
        anchorOffset=offset;
        foreach(var e in elements) { e.LambdaD=0; e.LambdaV=0; }
        foreach(var a in attachments) a.Lambda=default;
    }
    /// <summary>Translate the whole state without introducing impulse, e.g. a teleport.</summary>
    public void Translate(V3 delta)
    {
        if(!delta.IsFinite) throw new ArgumentException("Non-finite translation.");
        for(int i=0;i<x.Length;i++) x[i]+=delta;
        anchorOffset+=delta;
    }
    public void Step(double dt)=>Step(dt,anchorOffset);
    /// <summary>Linearly samples moving attachment translation across substeps; rotational anchors are not yet implemented.</summary>
    public void Step(double dt,V3 newAnchorOffset)
    {
        if(!double.IsFinite(dt)||dt<=0||dt>0.05) throw new ArgumentOutOfRangeException(nameof(dt),"Use fixed positive steps <= 50 ms.");
        if(!newAnchorOffset.IsFinite) throw new ArgumentException("Non-finite anchor target.");
        double h=dt/Settings.Substeps,decay=Math.Exp(-Settings.VelocityDrag*h);
        V3 oldAnchor=anchorOffset;
        for(int s=0;s<Settings.Substeps;s++)
        {
            V3 target=V3.Lerp(oldAnchor,newAnchorOffset,(s+1.0)/Settings.Substeps);
            for(int i=0;i<x.Length;i++)
            {
                previous[i]=x[i]; contactNormal[i]=default;
                if(invMass[i]>0) { v[i]=(v[i]+Settings.Gravity*h)*decay; x[i]+=v[i]*h; }
                freeVelocity[i]=v[i];
            }
            foreach(var e in elements) { e.LambdaD=0; e.LambdaV=0; }
            foreach(var a in attachments)
            {
                a.Lambda=default;
                if(a.Compliance==0) x[a.Index]=Mesh.RestPositions[a.Index]+target;
            }
            for(int k=0;k<Settings.Iterations;k++)
            {
                foreach(var e in elements) SolveElastic(e,h);
                foreach(var a in attachments) if(a.Compliance>0)
                {
                    int i=a.Index; double alpha=a.Compliance/(h*h);
                    V3 dl=(-(x[i]-Mesh.RestPositions[i]-target)-a.Lambda*alpha)/(invMass[i]+alpha);
                    a.Lambda+=dl; x[i]+=dl*invMass[i];
                }
                ProjectContacts();
            }
            for(int i=0;i<x.Length;i++)
            {
                v[i]=(x[i]-previous[i])/h;
                V3 n=contactNormal[i];
                if(n.LengthSquared>0 && invMass[i]>0)
                {
                    double vn=V3.Dot(v[i],n);
                    double normalCorrection=Math.Max(0,V3.Dot(v[i]-freeVelocity[i],n));
                    V3 tangent=v[i]-n*vn; double speed=tangent.Length;
                    double keep=speed>1e-12 ? Math.Max(0,1-Settings.Friction*normalCorrection/speed):0;
                    v[i]=n*Math.Max(0,vn)+tangent*keep;
                }
                if(!x[i].IsFinite||!v[i].IsFinite) throw new InvalidOperationException($"Non-finite solver state at particle {i}. Reset and inspect inputs.");
            }
        }
        anchorOffset=newAnchorOffset;
    }

    private void SolveElastic(Element e,double h)
    {
        var ids=e.Ids; M3 f=ids.EdgeMatrix(x)*e.Inverse;
        double norm=Math.Sqrt(f.NormSquared);
        if(norm<1e-12) return; // fully collapsed singular state: diagnostics must expose this; no fabricated recovery
        M3 gdMatrix=(f*(1/norm))*e.Inverse.Transposed;
        M3 gvMatrix=f.Cofactor*e.Inverse.Transposed;
        Span<V3> gd=stackalloc V3[4]; Span<V3> gv=stackalloc V3[4];
        gd[1]=gdMatrix.C0; gd[2]=gdMatrix.C1; gd[3]=gdMatrix.C2; gd[0]=-(gd[1]+gd[2]+gd[3]);
        gv[1]=gvMatrix.C0; gv[2]=gvMatrix.C1; gv[3]=gvMatrix.C2; gv[0]=-(gv[1]+gv[2]+gv[3]);
        double ad=1/(material.ShearModulus*e.Volume*h*h),av=1/(material.StableLambda*e.Volume*h*h);
        double dd=ad,vv=av,dv=0;
        for(int i=0;i<4;i++)
        {
            double w=invMass[ids[i]]; dd+=w*gd[i].LengthSquared; vv+=w*gv[i].LengthSquared; dv+=w*V3.Dot(gd[i],gv[i]);
        }
        double rd=-norm-ad*e.LambdaD,rv=-(f.Determinant-material.RestShift)-av*e.LambdaV;
        double det=dd*vv-dv*dv;
        if(!double.IsFinite(det)||det<=0) throw new InvalidOperationException("Invalid local elasticity system.");
        double ld=(rd*vv-rv*dv)/det,lv=(rv*dd-rd*dv)/det;
        e.LambdaD+=ld; e.LambdaV+=lv;
        for(int i=0;i<4;i++) x[ids[i]]+=(gd[i]*ld+gv[i]*lv)*invMass[ids[i]];
    }
    private void ProjectContacts()
    {
        for(int i=0;i<x.Length;i++) if(invMass[i]>0)
            foreach(var shape in Contacts)
            {
                double d=shape.Distance(x[i],out V3 n);
                if(d<Settings.ParticleRadius)
                { x[i]+=n*(Settings.ParticleRadius-d); contactNormal[i]=n; }
            }
    }
    public BodyDiagnostics Inspect()
    {
        double min=double.PositiveInfinity,error=0,energy=0; int inverted=0;
        bool finite=true;
        foreach(var e in elements)
        {
            double j=e.Ids.Volume(x)/e.Volume;
            min=Math.Min(min,j); error=Math.Max(error,Math.Abs(j-1)); if(j<=0) inverted++;
            finite&=double.IsFinite(j);
        }
        for(int i=0;i<x.Length;i++) { finite&=x[i].IsFinite&&v[i].IsFinite; energy+=0.5*mass[i]*v[i].LengthSquared; }
        return new(min,error,inverted,energy,finite);
    }
}
