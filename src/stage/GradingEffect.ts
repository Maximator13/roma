import { Effect } from 'postprocessing'
import { Uniform, Vector3 } from 'three'
import type { Grading } from './grading.ts'

const fragmentShader = `
uniform float exposure;
uniform float contrast;
uniform float saturation;
uniform vec3 lift;
uniform vec3 gain;

void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  vec3 color = max(inputColor.rgb * exposure, vec3(0.0));
  color = 0.18 * pow(color / 0.18, vec3(contrast));
  float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
  color = mix(vec3(luma), color, saturation);
  color = color * gain + lift * (1.0 - clamp(color, 0.0, 1.0));
  outputColor = vec4(color, inputColor.a);
}
`

export class GradingEffect extends Effect {
  constructor() {
    super('GradingEffect', fragmentShader, {
      uniforms: new Map<string, Uniform>([
        ['exposure', new Uniform(1)],
        ['contrast', new Uniform(1)],
        ['saturation', new Uniform(1)],
        ['lift', new Uniform(new Vector3())],
        ['gain', new Uniform(new Vector3(1, 1, 1))],
      ]),
    })
  }

  applyGrading(grading: Grading) {
    this.uniforms.get('exposure')!.value = grading.exposure
    this.uniforms.get('contrast')!.value = grading.contrast
    this.uniforms.get('saturation')!.value = grading.saturation
    ;(this.uniforms.get('lift')!.value as Vector3).fromArray(grading.lift)
    ;(this.uniforms.get('gain')!.value as Vector3).fromArray(grading.gain)
  }
}
