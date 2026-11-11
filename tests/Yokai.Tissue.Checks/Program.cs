using System.Numerics;
using Yokai.Tissue;

var volume = Tetrahedron.SignedVolume(Vector3.Zero, Vector3.UnitX, Vector3.UnitY, Vector3.UnitZ);
if (MathF.Abs(volume - 1f / 6f) > 1e-7f)
    throw new InvalidOperationException($"Signed-volume convention failed: {volume}");
Console.WriteLine("PASS: positive right-handed unit tetrahedron volume = 1/6 m^3");
Console.WriteLine("Bootstrap check only; no tissue simulation or character is validated yet.");
