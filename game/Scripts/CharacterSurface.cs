using Godot;
using Yokai.Tissue;
using GArray=Godot.Collections.Array;

namespace YokaiDominion;

/// <summary>CPU reference morph -> skin -> tissue path. Mesh rebuilds are not the final GPU backend.</summary>
internal sealed class CharacterSurface
{
    public MeshInstance3D Source {get;}
    public MeshInstance3D Display {get;}
    public int BoundVertices=>surfaces.Sum(s=>s.Maps.Sum(m=>m.Vertices.Length));
    public float MaxDisplacement {get;private set;}
    public float RestSkinError {get;private set;}
    private readonly Skeleton3D skeleton;
    private readonly Skin skin;
    private readonly CharacterTissueRegion[] regions;
    private readonly Surface[] surfaces;
    private readonly Transform3D[] matrices;
    private readonly int[] boneIndices;
    private readonly ArrayMesh output=new();
    private sealed class Surface
    {
        public Vector3[] Rest=[],Normals=[],Position=[];
        public Vector2[] UV=[];
        public Color[] Colors=[];
        public int[] Indices=[],Joints=[];
        public float[] Weights=[];
        public Vector3[][] MorphDeltas=[];
        public Material? Material;
        public TissueSurfaceMap[] Maps=[];
        public V3[] Delta=[];
        public double[] Coverage=[];
    }
    public static V3 ToCore(Vector3 p)=>new(p.X,p.Y,p.Z);
    public static Vector3 ToGodot(V3 p)=>new((float)p.X,(float)p.Y,(float)p.Z);
    public CharacterSurface(Node3D owner,MeshInstance3D source,Skeleton3D rig,CharacterTissueRegion[] regions)
    {
        Source=source; skeleton=rig; this.regions=regions; skin=source.Skin??throw new InvalidOperationException("Mesh is not skinned.");
        if(source.Mesh is not ArrayMesh mesh) throw new InvalidOperationException("Expected imported ArrayMesh.");
        matrices=new Transform3D[skin.GetBindCount()]; boneIndices=new int[matrices.Length];
        for(int i=0;i<matrices.Length;i++)
        {
            int b=skin.GetBindBone(i); if(b<0)b=skeleton.FindBone(skin.GetBindName(i));
            if(b<0)throw new InvalidOperationException("Unresolved skin bind."); boneIndices[i]=b;
        }
        surfaces=new Surface[mesh.GetSurfaceCount()];
        for(int k=0;k<surfaces.Length;k++)
        {
            var a=mesh.SurfaceGetArrays(k); var s=new Surface(); surfaces[k]=s;
            s.Rest=a[(int)Mesh.ArrayType.Vertex].AsVector3Array(); s.Normals=a[(int)Mesh.ArrayType.Normal].AsVector3Array();
            s.Indices=a[(int)Mesh.ArrayType.Index].AsInt32Array(); s.Joints=a[(int)Mesh.ArrayType.Bones].AsInt32Array(); s.Weights=a[(int)Mesh.ArrayType.Weights].AsFloat32Array();
            if(a[(int)Mesh.ArrayType.TexUV].VariantType!=Variant.Type.Nil)s.UV=a[(int)Mesh.ArrayType.TexUV].AsVector2Array();
            if(a[(int)Mesh.ArrayType.Color].VariantType!=Variant.Type.Nil)s.Colors=a[(int)Mesh.ArrayType.Color].AsColorArray();
            if(s.Joints.Length!=4*s.Rest.Length||s.Weights.Length!=s.Joints.Length)throw new InvalidOperationException("Expected four skin influences.");
            s.Material=CharacterMaterials.ForSurface(source,k); s.Position=new Vector3[s.Rest.Length]; s.Delta=new V3[s.Rest.Length];s.Coverage=new double[s.Rest.Length];
            var shapeArrays=mesh.SurfaceGetBlendShapeArrays(k); s.MorphDeltas=new Vector3[shapeArrays.Count][];
            for(int m=0;m<shapeArrays.Count;m++)
            {
                var p=shapeArrays[m][(int)Mesh.ArrayType.Vertex].AsVector3Array();
                s.MorphDeltas[m]=p.Select((v,i)=>mesh.BlendShapeMode==Mesh.BlendShapeMode.Normalized?v-s.Rest[i]:v).ToArray();
            }
            var bindWorld=s.Rest.Select(p=>ToCore(source.GlobalTransform*p)).ToArray();
            s.Maps=regions.Select(r=>r.Bind(bindWorld)).ToArray();
        }
        Display=new MeshInstance3D{Name=source.Name+"_Runtime",Mesh=output}; owner.AddChild(Display); Source.Visible=false;
        Update(false,true);
        if(RestSkinError>.002f)throw new InvalidOperationException($"{source.Name}: CPU rest skin mismatch {RestSkinError} m; inspect bind matrices/coordinate conversion.");
    }
    public void SetPhysics(bool enabled) {Source.Visible=!enabled;Display.Visible=enabled;}
    public void Update(bool tissue,bool measureRest=false)
    {
        for(int i=0;i<matrices.Length;i++)matrices[i]=skeleton.GlobalTransform*skeleton.GetBoneGlobalPose(boneIndices[i])*skin.GetBindPose(i);
        output.ClearSurfaces(); MaxDisplacement=0;
        foreach(var s in surfaces)
        {
            Array.Clear(s.Delta);Array.Clear(s.Coverage);
            if(tissue)for(int r=0;r<regions.Length;r++)s.Maps[r].Accumulate(regions[r],s.Delta,s.Coverage);
            var morphWeights=Enumerable.Range(0,s.MorphDeltas.Length).Select(Source.GetBlendShapeValue).ToArray();
            for(int i=0;i<s.Rest.Length;i++)
            {
                Vector3 p=s.Rest[i]; for(int m=0;m<morphWeights.Length;m++)p+=s.MorphDeltas[m][i]*morphWeights[m];
                Vector3 skinned=Vector3.Zero;
                for(int j=0;j<4;j++)if(s.Weights[i*4+j]>0)skinned+=(matrices[s.Joints[i*4+j]]*p)*s.Weights[i*4+j];
                if(measureRest)RestSkinError=Math.Max(RestSkinError,skinned.DistanceTo(Source.GlobalTransform*s.Rest[i]));
                var delta=ToGodot(TissueSurfaceMap.NormalizeAccumulated(s.Delta[i],s.Coverage[i]));
                MaxDisplacement=Math.Max(MaxDisplacement,delta.Length());s.Position[i]=skinned+delta;
                if(!s.Position[i].IsFinite())throw new InvalidOperationException("Nonfinite rendered vertex.");
            }
            Vector3[] normals=new Vector3[s.Position.Length];
            for(int i=0;i<s.Indices.Length;i+=3)
            {
                int a=s.Indices[i],b=s.Indices[i+1],c=s.Indices[i+2];
                var normal=(s.Position[c]-s.Position[a]).Cross(s.Position[b]-s.Position[a]);
                normals[a]+=normal;normals[b]+=normal;normals[c]+=normal;
            }
            for(int i=0;i<normals.Length;i++)normals[i]=normals[i].LengthSquared()>1e-14f?normals[i].Normalized():Vector3.Up;
            GArray arrays=[];arrays.Resize((int)Mesh.ArrayType.Max);arrays[(int)Mesh.ArrayType.Vertex]=s.Position;arrays[(int)Mesh.ArrayType.Normal]=normals;arrays[(int)Mesh.ArrayType.Index]=s.Indices;
            if(s.UV.Length>0)arrays[(int)Mesh.ArrayType.TexUV]=s.UV;if(s.Colors.Length>0)arrays[(int)Mesh.ArrayType.Color]=s.Colors;
            output.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles,arrays);output.SurfaceSetMaterial(output.GetSurfaceCount()-1,s.Material);
        }
    }
}
