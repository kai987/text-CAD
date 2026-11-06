import { DoubleSide, Mesh, PlaneGeometry, ShaderMaterial, Vector3 } from 'three';
import type { Box3 } from 'three';

const vertexShader = `
  varying vec3 vWaterWorld;
  void main() {
    vec4 world = modelMatrix * vec4(position, 1.0);
    vWaterWorld = world.xyz;
    gl_Position = projectionMatrix * viewMatrix * world;
  }
`;
const fragmentShader = `
  precision highp float;
  uniform float uTime;
  uniform float uNight;
  varying vec3 vWaterWorld;
  float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453123); }
  float noise21(vec2 p) {
    vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(hash21(i),hash21(i+vec2(1.0,0.0)),f.x),mix(hash21(i+vec2(0.0,1.0)),hash21(i+vec2(1.0,1.0)),f.x),f.y);
  }
  void wave(inout vec3 result, vec2 p, vec2 direction, float frequency, float amplitude, float speed) {
    // Independent, slowly varying wave packets avoid endless parallel ridges.
    vec2 seed=direction*19.7;
    float packet=noise21(p*0.055+seed+vec2(uTime*0.014,-uTime*0.009));
    float phase=noise21(p*0.029-seed)*5.4;
    float angle=dot(p,direction)*frequency + phase + uTime*speed;
    float strength=amplitude*(0.25+1.15*packet*packet);
    // Suppress subpixel ripples in overview without changing their real scale.
    float footprint=length(fwidth(p))*frequency;
    float lod=1.0-smoothstep(0.35,2.1,footprint);
    result += vec3(strength*sin(angle), strength*frequency*cos(angle)*direction) * lod;
  }
  void main() {
    vec2 p=vWaterWorld.xz;
    vec2 drift=vec2(uTime*0.035,-uTime*0.018);
    vec2 warped=p+12.0*vec2(noise21(p*0.033+drift),noise21(p*0.031+vec2(31.7,9.2)-drift));
    vec3 sea=vec3(0.0);
    wave(sea,warped,normalize(vec2(0.72,0.69)),0.31,0.18,-0.60);
    wave(sea,warped,normalize(vec2(-0.84,0.54)),0.79,0.075,0.94);
    wave(sea,warped,normalize(vec2(0.42,0.91)),2.7,0.026,-1.63);
    wave(sea,warped,normalize(vec2(0.96,-0.28)),6.1,0.009,2.18);
    float smallLod=1.0-smoothstep(0.35,1.5,length(fwidth(p))*0.74);
    vec2 capillary=vec2(noise21(p*0.74+drift*2.0),noise21(p*0.69+vec2(7.6,38.1)-drift*2.0))-0.5;
    vec3 normal=normalize(vec3(-sea.y+capillary.x*0.11*smallLod,1.0,-sea.z+capillary.y*0.11*smallLod));
    vec3 eye=normalize(cameraPosition-vWaterWorld);
    vec3 sun=normalize(vec3(-0.42,0.84,0.35));
    float fresnel=0.04+0.65*pow(1.0-max(dot(normal,eye),0.0),4.0);
    vec3 halfLight=normalize(sun+eye);
    float shimmer=pow(max(dot(normal,halfLight),0.0),48.0);
    float swell=noise21(p*0.017+vec2(uTime*0.012,-uTime*0.008));
    float flecks=noise21(warped*0.31+drift*1.6);
    float brokenCrest=smoothstep(0.08,0.25,sea.x)*smoothstep(0.35,0.8,flecks);
    vec3 deep=mix(vec3(0.019,0.125,0.177),vec3(0.006,0.025,0.055),uNight);
    vec3 sky=mix(vec3(0.38,0.65,0.73),vec3(0.025,0.09,0.15),uNight);
    vec3 colour=mix(deep,sky,clamp(fresnel+0.10*swell+0.025*flecks*smallLod,0.0,0.9));
    colour *= 0.88 + 0.20*max(dot(normal,sun),0.0) + 0.035*sea.x;
    colour += mix(vec3(0.78,0.88,0.85),vec3(0.08,0.17,0.24),uNight)*shimmer*(0.2+0.7*flecks);
    // Fragmented highlights, rather than a continuous painted colour band.
    colour += mix(vec3(0.018,0.036,0.039),vec3(0.002,0.006,0.009),uNight)*brokenCrest;
    gl_FragColor=vec4(colour,1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

/** Display-only, untextured sea surface; the downloadable CAD mean sea is untouched. */
export function createBridgeWater(bounds: Box3) {
  const size = bounds.getSize(new Vector3()), centre = bounds.getCenter(new Vector3());
  if (!Number.isFinite(size.x) || !Number.isFinite(size.z) || size.x <= 0 || size.z <= 0) throw new Error('Invalid bridge water extent.');
  const material = new ShaderMaterial({ vertexShader, fragmentShader,
    uniforms: { uTime: { value: 0 }, uNight: { value: 0 } }, side: DoubleSide,
    depthWrite: true, transparent: false, toneMapped: true });
  const geometry = new PlaneGeometry(size.x, size.z, 1, 1);
  geometry.rotateX(-Math.PI / 2);
  const mesh = new Mesh(geometry, material); mesh.position.set(centre.x, bounds.max.y + .025, centre.z);
  mesh.name = 'environment:display_only_procedural_water'; mesh.userData.bridgeGroup = 'environment';
  mesh.renderOrder = -1;
  return { mesh, time(seconds: number) { material.uniforms.uTime.value = Number.isFinite(seconds) ? seconds : 0; },
    night(value: boolean) { material.uniforms.uNight.value = value ? 1 : 0; },
    dispose() { geometry.dispose(); material.dispose(); } };
}

export const bridgeWaterShaderProfile = { version: 1, wavelengthsM: [2*Math.PI/.31,2*Math.PI/.79,2*Math.PI/2.7,2*Math.PI/6.1],
  procedural: true, externalTextures: false, animatedNormals: true, distanceFiltered: true } as const;
