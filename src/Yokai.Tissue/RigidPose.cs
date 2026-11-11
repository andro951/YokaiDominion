namespace Yokai.Tissue;

/// <summary>Unit quaternion in double precision. default(Q4) is intentionally invalid.</summary>
public readonly record struct Q4
{
    public double X { get; }
    public double Y { get; }
    public double Z { get; }
    public double W { get; }
    public static Q4 Identity=>new(0,0,0,1);
    public bool IsValid=>double.IsFinite(X)&&double.IsFinite(Y)&&double.IsFinite(Z)&&double.IsFinite(W)&&Math.Abs(X*X+Y*Y+Z*Z+W*W-1)<1e-10;
    public Q4(double x,double y,double z,double w)
    {
        double length=Math.Sqrt(x*x+y*y+z*z+w*w);
        if(!double.IsFinite(length)||length<1e-12) throw new ArgumentException("Quaternion must be finite and nonzero.");
        X=x/length; Y=y/length; Z=z/length; W=w/length;
    }
    public static Q4 FromAxisAngle(V3 axis,double radians)
    {
        if(!axis.IsFinite||!double.IsFinite(radians)) throw new ArgumentException("Invalid axis/angle.");
        V3 n=axis.Normalized(); double s=Math.Sin(radians/2);
        return new(n.X*s,n.Y*s,n.Z*s,Math.Cos(radians/2));
    }
    public V3 Rotate(V3 point)
    {
        V3 q=new(X,Y,Z),t=2*V3.Cross(q,point);
        return point+W*t+V3.Cross(q,t);
    }
    public Q4 Inverse=>new(-X,-Y,-Z,W);
    public static Q4 operator *(Q4 a,Q4 b)=>new(
        a.W*b.X+a.X*b.W+a.Y*b.Z-a.Z*b.Y,
        a.W*b.Y-a.X*b.Z+a.Y*b.W+a.Z*b.X,
        a.W*b.Z+a.X*b.Y-a.Y*b.X+a.Z*b.W,
        a.W*b.W-a.X*b.X-a.Y*b.Y-a.Z*b.Z);
    public static Q4 Slerp(Q4 a,Q4 b,double t)
    {
        if(!a.IsValid||!b.IsValid||!double.IsFinite(t)||t<0||t>1) throw new ArgumentException("Invalid quaternion interpolation.");
        double dot=a.X*b.X+a.Y*b.Y+a.Z*b.Z+a.W*b.W;
        double sign=dot<0?-1:1; dot=Math.Clamp(Math.Abs(dot),0,1);
        double wa=1-t,wb=t;
        if(dot<0.9995)
        {
            double angle=Math.Acos(dot),sin=Math.Sin(angle);
            wa=Math.Sin((1-t)*angle)/sin; wb=Math.Sin(t*angle)/sin;
        }
        wb*=sign;
        return new(a.X*wa+b.X*wb,a.Y*wa+b.Y*wb,a.Z*wa+b.Z*wb,a.W*wa+b.W*wb);
    }
}

/// <summary>Rigid delta from simulation rest coordinates to current world coordinates.</summary>
public readonly record struct RigidPose(V3 Translation,Q4 Rotation)
{
    public static RigidPose Identity=>new(V3.Zero,Q4.Identity);
    public bool IsValid=>Translation.IsFinite&&Rotation.IsValid;
    public V3 TransformPoint(V3 point)=>Rotation.Rotate(point)+Translation;
    public static RigidPose FromTranslation(V3 offset)=>new(offset,Q4.Identity);
    public static RigidPose AroundPivot(Q4 rotation,V3 pivot,V3 offset=default)=>new(pivot+offset-rotation.Rotate(pivot),rotation);
    public RigidPose Inverse=>new(Rotation.Inverse.Rotate(-Translation),Rotation.Inverse);
    public static RigidPose operator *(RigidPose a,RigidPose b)=>new(a.TransformPoint(b.Translation),a.Rotation*b.Rotation);
    public static RigidPose Interpolate(RigidPose a,RigidPose b,double t)=>new(V3.Lerp(a.Translation,b.Translation,t),Q4.Slerp(a.Rotation,b.Rotation,t));
}
