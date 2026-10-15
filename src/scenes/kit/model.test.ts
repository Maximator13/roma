import { Group, Mesh } from 'three'
import { describe, expect, it } from 'vitest'
import { castsShadow } from './model.ts'

describe('castsShadow', () => {
  it('follows the nearest cast_shadow flag exported from Blender', () => {
    const group = new Group()
    group.userData.cast_shadow = false
    const mesh = new Mesh()
    group.add(mesh)
    expect(castsShadow(mesh)).toBe(false)
    mesh.userData.cast_shadow = true
    expect(castsShadow(mesh)).toBe(true)
  })

  it('casts shadows by default', () => {
    expect(castsShadow(new Mesh())).toBe(true)
  })
})
