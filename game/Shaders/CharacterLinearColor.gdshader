shader_type spatial;
render_mode cull_disabled;

// glTF COLOR_0 is linear. Compatibility shades ALBEDO in sRGB, while
// Forward+/Mobile shade in linear space. Do not change the source palette.
vec3 linear_to_srgb(vec3 color) {
    vec3 c = max(color, vec3(0.0));
    return mix(1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055,
               c * 12.92, lessThanEqual(c, vec3(0.0031308)));
}

void fragment() {
    ALBEDO = OUTPUT_IS_SRGB ? linear_to_srgb(COLOR.rgb) : COLOR.rgb;
    METALLIC = 0.0;
    ROUGHNESS = 0.62;
}
