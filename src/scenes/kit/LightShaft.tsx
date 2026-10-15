import { useEffect, useMemo } from 'react'
import { AdditiveBlending, CylinderGeometry, DoubleSide, Matrix4, Mesh, Quaternion, ShaderMaterial, Vector3 } from 'three'


const vertexShader = [
  'varying vec2 vUv;',
  'varying vec3 vNormalView;',
  'varying vec3 vViewDirection;',
  'void main() {',
  '  vUv = uv;',
  '  vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);',
  '  vNormalView = normalize(normalMatrix * normal);',
  '  vViewDirection = normalize(-viewPosition.xyz);',
  '  gl_Position = projectionMatrix * viewPosition;',
  '}',
].join('\n')

const fragmentShader = [
  'uniform vec3 color;',
  'uniform float strength;',
  'varying vec2 vUv;',
  'varying vec3 vNormalView;',
  'varying vec3 vViewDirection;',
  'void main() {',
  '  float facing = abs(dot(normalize(vNormalView), normalize(vViewDirection)));',
  '  float along = smoothstep(0.0, 0.12, vUv.y) * smoothstep(1.0, 0.95, vUv.y);',
  '  gl_FragColor = vec4(color * strength * facing * facing * along, 1.0);',
  '}',
].join('\n')

export function LightShaft({ from, to, radius }: { from: Vector3; to: Vector3; radius: number }) {
  const shaft = useMemo(() => {
    const length = from.distanceTo(to)
    const geometry = new CylinderGeometry(radius, radius * 1.08, length, 48, 1, true)
    const material = new ShaderMaterial({
      uniforms: { color: { value: new Vector3(1, 0.92, 0.78) }, strength: { value: 0.22 } },
      vertexShader,
      fragmentShader,
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
      side: DoubleSide,
    })
    const mesh = new Mesh(geometry, material)
    const direction = new Vector3().subVectors(from, to).normalize()
    const rotation = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), direction)
    const middle = new Vector3().addVectors(from, to).multiplyScalar(0.5)
    mesh.applyMatrix4(new Matrix4().compose(middle, rotation, new Vector3(1, 1, 1)))
    mesh.renderOrder = 3
    return mesh
  }, [from, to, radius])
  useEffect(
    () => () => {
      shaft.geometry.dispose()
      ;(shaft.material as ShaderMaterial).dispose()
    },
    [shaft],
  )
  return <primitive object={shaft} />
}
