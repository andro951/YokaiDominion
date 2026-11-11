namespace Yokai.Tissue;

/// <summary>Signed distance: negative inside. Normal points out. World-space SI units.</summary>
public interface IContactShape
{
    double Distance(V3 point,out V3 normal);
}

public sealed class ContactPlane : IContactShape
{
    private readonly V3 normal;
    private readonly double offset;
    public ContactPlane(V3 normal,double offset)
    {
        if(!normal.IsFinite||!double.IsFinite(offset)||normal.Length<1e-12) throw new ArgumentException("Invalid plane.");
        double length=normal.Length; this.normal=normal/length; this.offset=offset/length;
    }
    public double Distance(V3 point,out V3 outward) { outward=normal; return V3.Dot(normal,point)-offset; }
}

public sealed class ContactCapsule : IContactShape
{
    public V3 A { get; }
    public V3 B { get; }
    public double Radius { get; }
    public ContactCapsule(V3 a,V3 b,double radius)
    {
        if(!a.IsFinite||!b.IsFinite||!double.IsFinite(radius)||radius<=0) throw new ArgumentException("Invalid capsule.");
        A=a; B=b; Radius=radius;
    }
    public double Distance(V3 point,out V3 normal)
    {
        V3 ab=B-A;
        double t=ab.LengthSquared>1e-20 ? Math.Clamp(V3.Dot(point-A,ab)/ab.LengthSquared,0,1):0;
        V3 d=point-(A+ab*t); double length=d.Length;
        // On the axis choose a deterministic perpendicular direction, not the capsule axis.
        V3 fallback=ab.LengthSquared>1e-20 ? V3.Cross(ab,Math.Abs(ab.Normalized().X)<0.9 ? V3.UnitX:V3.UnitY).Normalized():V3.UnitX;
        normal=length>1e-12 ? d/length : fallback;
        return length-Radius;
    }
}
