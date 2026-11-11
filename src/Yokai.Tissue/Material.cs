namespace Yokai.Tissue;

/// <summary>Isotropic elastic baseline, not calibrated biological tissue. SI units.</summary>
public sealed class TissueMaterial
{
    public double YoungModulus { get; }
    public double PoissonRatio { get; }
    public double Density { get; }
    public double ShearModulus { get; }
    public double StableLambda { get; }
    public double RestShift => 1+ShearModulus/StableLambda;
    public TissueMaterial(double youngModulus=8000,double poissonRatio=0.47,double density=1000)
    {
        if(!double.IsFinite(youngModulus)||youngModulus<=0) throw new ArgumentOutOfRangeException(nameof(youngModulus));
        if(!double.IsFinite(poissonRatio)||poissonRatio<0||poissonRatio>=0.5) throw new ArgumentOutOfRangeException(nameof(poissonRatio));
        if(!double.IsFinite(density)||density<=0) throw new ArgumentOutOfRangeException(nameof(density));
        YoungModulus=youngModulus; PoissonRatio=poissonRatio; Density=density;
        ShearModulus=youngModulus/(2*(1+poissonRatio));
        // The +mu correction makes the stable energy match the requested small-strain Lamé parameters.
        StableLambda=youngModulus*poissonRatio/((1+poissonRatio)*(1-2*poissonRatio))+ShearModulus;
    }
}

public static class NeoHookean
{
    public static double EnergyDensity(M3 f,TissueMaterial m)
    {
        double j=f.Determinant-1;
        return 0.5*m.ShearModulus*(f.NormSquared-3)-m.ShearModulus*j+0.5*m.StableLambda*j*j;
    }
    public static M3 FirstPiola(M3 f,TissueMaterial m) =>
        f*m.ShearModulus+f.Cofactor*(m.StableLambda*(f.Determinant-1)-m.ShearModulus);
}

public sealed record SolverSettings
{
    public int Substeps { get; init; }=4;
    public int Iterations { get; init; }=4;
    public double VelocityDrag { get; init; }=0.6;
    public double ParticleRadius { get; init; }=0.003;
    public double Friction { get; init; }=0.35;
    public V3 Gravity { get; init; }=new(0,-9.81,0);
    public void Validate()
    {
        if(Substeps<1||Substeps>128||Iterations<1||Iterations>128) throw new ArgumentOutOfRangeException(nameof(Substeps));
        if(!Gravity.IsFinite||!double.IsFinite(VelocityDrag)||VelocityDrag<0||!double.IsFinite(ParticleRadius)||ParticleRadius<0||!double.IsFinite(Friction)||Friction<0)
            throw new ArgumentException("Invalid solver parameters.");
    }
}
