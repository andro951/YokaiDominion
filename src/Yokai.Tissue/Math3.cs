namespace Yokai.Tissue;

/// <summary>Double precision, engine-independent world-space vector (metres).</summary>
public readonly record struct V3(double X, double Y, double Z)
{
    public static V3 Zero => default;
    public static V3 UnitX => new(1, 0, 0);
    public static V3 UnitY => new(0, 1, 0);
    public static V3 UnitZ => new(0, 0, 1);
    public double LengthSquared => Dot(this, this);
    public double Length => Math.Sqrt(LengthSquared);
    public bool IsFinite => double.IsFinite(X) && double.IsFinite(Y) && double.IsFinite(Z);
    public static double Dot(V3 a, V3 b) => a.X * b.X + a.Y * b.Y + a.Z * b.Z;
    public static V3 Cross(V3 a, V3 b) => new(a.Y*b.Z-a.Z*b.Y, a.Z*b.X-a.X*b.Z, a.X*b.Y-a.Y*b.X);
    public static V3 Lerp(V3 a, V3 b, double t) => a + (b-a)*t;
    public V3 Normalized() => Length > 1e-15 ? this / Length : throw new ArgumentException("Cannot normalize a zero vector.");
    public double this[int axis] => axis switch { 0 => X, 1 => Y, 2 => Z, _ => throw new ArgumentOutOfRangeException(nameof(axis)) };
    public V3 With(int axis, double value) => axis switch { 0 => this with { X=value }, 1 => this with { Y=value }, 2 => this with { Z=value }, _ => throw new ArgumentOutOfRangeException(nameof(axis)) };
    public static V3 operator +(V3 a, V3 b) => new(a.X+b.X, a.Y+b.Y, a.Z+b.Z);
    public static V3 operator -(V3 a, V3 b) => new(a.X-b.X, a.Y-b.Y, a.Z-b.Z);
    public static V3 operator -(V3 a) => a * -1;
    public static V3 operator *(V3 a, double s) => new(a.X*s, a.Y*s, a.Z*s);
    public static V3 operator *(double s, V3 a) => a*s;
    public static V3 operator /(V3 a, double s) => a*(1/s);
}

/// <summary>Column-major 3x3 matrix. All physics uses column-vector convention.</summary>
public readonly record struct M3(V3 C0, V3 C1, V3 C2)
{
    public static M3 Identity => new(V3.UnitX, V3.UnitY, V3.UnitZ);
    public V3 this[int column] => column switch { 0=>C0, 1=>C1, 2=>C2, _=>throw new ArgumentOutOfRangeException(nameof(column)) };
    public M3 Transposed => new(new(C0.X,C1.X,C2.X), new(C0.Y,C1.Y,C2.Y), new(C0.Z,C1.Z,C2.Z));
    public M3 Cofactor => new(V3.Cross(C1,C2), V3.Cross(C2,C0), V3.Cross(C0,C1));
    public double Determinant => V3.Dot(C0,V3.Cross(C1,C2));
    public double NormSquared => C0.LengthSquared+C1.LengthSquared+C2.LengthSquared;
    public M3 Inverse()
    {
        double d=Determinant;
        if (!double.IsFinite(d) || Math.Abs(d)<1e-15) throw new ArgumentException("Singular matrix.");
        return Cofactor.Transposed*(1/d);
    }
    public static V3 operator *(M3 a,V3 v)=>a.C0*v.X+a.C1*v.Y+a.C2*v.Z;
    public static M3 operator *(M3 a,M3 b)=>new(a*b.C0,a*b.C1,a*b.C2);
    public static M3 operator *(M3 a,double s)=>new(a.C0*s,a.C1*s,a.C2*s);
    public static M3 operator +(M3 a,M3 b)=>new(a.C0+b.C0,a.C1+b.C1,a.C2+b.C2);
    public static M3 operator -(M3 a,M3 b)=>new(a.C0-b.C0,a.C1-b.C1,a.C2-b.C2);
    public static M3 RotationY(double radians) => new(new(Math.Cos(radians),0,-Math.Sin(radians)), V3.UnitY, new(Math.Sin(radians),0,Math.Cos(radians)));
}
