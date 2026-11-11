using Godot;

namespace YokaiDominion;

/// <summary>Explicit glTF linear vertex-colour policy shared by native skinning and the CPU reference path.</summary>
internal static class CharacterMaterials
{
    public static Material? ForSurface(MeshInstance3D source, int surface)
    {
        var material = source.GetActiveMaterial(surface);
        var arrays = source.Mesh.SurfaceGetArrays(surface);
        if (arrays[(int)Mesh.ArrayType.Color].VariantType == Variant.Type.Nil)
            return material;
        if (material is not StandardMaterial3D standard)
            throw new InvalidOperationException("The character colour stream requires an explicit StandardMaterial3D policy.");
        var result = (StandardMaterial3D)standard.Duplicate();
        result.VertexColorUseAsAlbedo = true;
        result.VertexColorIsSrgb = false; // glTF COLOR_0 is linear, and Blender authoring writes linear floats.
        result.AlbedoColor = Colors.White;
        result.Metallic = 0;
        result.Roughness = .62f;
        source.SetSurfaceOverrideMaterial(surface, result);
        return result;
    }
}
