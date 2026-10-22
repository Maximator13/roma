import { useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import { CanvasTexture, Color, InstancedMesh, Matrix4, MeshBasicMaterial, PlaneGeometry, Vector3, type Box3 } from 'three'
import { prefersReducedMotion } from '../../core/motion.ts'

const PUFFS_PER_CLOUD = 5
const WIND = new Vector3(6, 0, 2.5)

function seeded(index: number): number {
  const value = Math.sin(index * 91.7 + 47.3) * 43758.5453
  return value - Math.floor(value)
}

function cloudTexture(): CanvasTexture {
  const size = 256
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size
  const context = canvas.getContext('2d')!
  for (let blob = 0; blob < 14; blob += 1) {
    const x = size * (0.28 + 0.44 * seeded(blob))
    const y = size * (0.36 + 0.3 * seeded(blob + 40))
    const radius = size * (0.12 + 0.16 * seeded(blob + 80))
    const gradient = context.createRadialGradient(x, y, 0, x, y, radius)
    gradient.addColorStop(0, 'rgba(255,255,255,0.8)')
    gradient.addColorStop(0.6, 'rgba(255,255,255,0.35)')
    gradient.addColorStop(1, 'rgba(255,255,255,0)')
    context.fillStyle = gradient
    context.fillRect(0, 0, size, size)
  }
  context.globalCompositeOperation = 'source-atop'
  const shade = context.createLinearGradient(0, size * 0.2, 0, size * 0.8)
  shade.addColorStop(0, 'rgba(255,255,255,0)')
  shade.addColorStop(1, 'rgba(150,160,175,0.75)')
  context.fillStyle = shade
  context.fillRect(0, 0, size, size)
  return new CanvasTexture(canvas)
}

interface Puff {
  position: Vector3
  scale: number
}

export function Clouds({ bounds, cover, sunColor }: { bounds: Box3; cover: number; sunColor: string }) {
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const layout = useMemo(() => {
    const centre = bounds.getCenter(new Vector3())
    const reach = Math.min(4500, Math.max(2000, bounds.getSize(new Vector3()).length() * 0.5))
    const clouds = Math.max(4, Math.round(70 * cover))
    const puffs: Puff[] = []
    for (let cloud = 0; cloud < clouds; cloud += 1) {
      const angle = seeded(cloud) * Math.PI * 2
      const high = cloud % 2 === 0
      const distance = reach * (high ? 0.3 + 1.1 * seeded(cloud + 200) : 0.9 + 1.5 * seeded(cloud + 200))
      const altitude = high ? 1300 + 1100 * seeded(cloud + 400) : 450 + 900 * seeded(cloud + 400)
      const base = new Vector3(centre.x + Math.cos(angle) * distance, centre.y + altitude, centre.z + Math.sin(angle) * distance)
      const width = (high ? 700 : 500) + 900 * seeded(cloud + 600)
      for (let puff = 0; puff < PUFFS_PER_CLOUD; puff += 1) {
        const index = cloud * PUFFS_PER_CLOUD + puff
        const offset = (puff / (PUFFS_PER_CLOUD - 1) - 0.5) * width
        puffs.push({
          position: base.clone().add(new Vector3(offset, (seeded(index + 800) - 0.3) * width * 0.25, (seeded(index + 900) - 0.5) * width * 0.3)),
          scale: width * (0.55 + 0.35 * seeded(index + 1000)) * (puff === 0 || puff === PUFFS_PER_CLOUD - 1 ? 0.7 : 1),
        })
      }
    }
    return { puffs, centre, reach }
  }, [bounds, cover])
  const mesh = useMemo(() => {
    const material = new MeshBasicMaterial({ map: cloudTexture(), transparent: true, depthWrite: false, fog: true })
    material.color.set('#ffffff').lerp(new Color(sunColor), 0.35)
    const instanced = new InstancedMesh(new PlaneGeometry(1, 1), material, layout.puffs.length)
    instanced.frustumCulled = false
    instanced.renderOrder = 1
    return instanced
  }, [layout, sunColor])
  const live = useRef(mesh)
  useEffect(() => {
    live.current = mesh
    return () => {
      const material = mesh.material as MeshBasicMaterial
      material.map?.dispose()
      material.dispose()
      mesh.geometry.dispose()
      mesh.dispose()
    }
  }, [mesh])
  const scratchRef = useRef({ matrix: new Matrix4(), position: new Vector3(), scale: new Vector3() })

  useFrame(({ clock, camera }) => {
    const time = reducedMotion ? 0 : clock.elapsedTime
    const scratch = scratchRef.current
    const span = layout.reach * 4
    layout.puffs.forEach((puff, index) => {
      scratch.position.copy(puff.position).addScaledVector(WIND, time)
      const dx = scratch.position.x - layout.centre.x
      scratch.position.x = layout.centre.x + ((((dx + span / 2) % span) + span) % span) - span / 2
      scratch.scale.set(puff.scale, puff.scale * 0.55, 1)
      scratch.matrix.compose(scratch.position, camera.quaternion, scratch.scale)
      live.current.setMatrixAt(index, scratch.matrix)
    })
    live.current.instanceMatrix.needsUpdate = true
  })

  return <primitive object={mesh} />
}
