using System.Numerics;

namespace Yokai.Tissue;

/// <summary>Vertex indices of an oriented tetrahedral element. Distances are metres.</summary>
public readonly record struct Tetrahedron(int A, int B, int C, int D)
{
    public static float SignedVolume(Vector3 a, Vector3 b, Vector3 c, Vector3 d) =>
        Vector3.Dot(b - a, Vector3.Cross(c - a, d - a)) / 6f;

    public float Volume(ReadOnlySpan<Vector3> positions) =>
        SignedVolume(positions[A], positions[B], positions[C], positions[D]);
}
