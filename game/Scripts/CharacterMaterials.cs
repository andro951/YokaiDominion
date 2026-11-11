using Godot;

namespace YokaiDominion;

/// <summary>One linear glTF colour policy for native skinning and the CPU deformation mesh.</summary>
internal static class CharacterMaterials
{
    public const string ShaderPath = "res://Shaders/CharacterLinearColor.gdshader";
    public static Material? ForSurface(MeshInstance3D source, int surface)
    {
        var arrays = source.Mesh.SurfaceGetArrays(surface);
        if (arrays[(int)Mesh.ArrayType.Color].VariantType == Variant.Type.Nil)
            return source.GetActiveMaterial(surface);
        var result = new ShaderMaterial { Shader = GD.Load<Shader>(ShaderPath) };
        source.SetSurfaceOverrideMaterial(surface, result);
        return result;
    }
    public static bool HasLinearColorPolicy(Material? material) =>
        material is ShaderMaterial shader && shader.Shader?.ResourcePath == ShaderPath;
}
