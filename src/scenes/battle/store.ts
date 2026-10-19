import { create } from 'zustand'

export type BattleView = 'tactical' | 'ground'

interface BattleState {
  time: number
  playing: boolean
  view: BattleView
  controlsHeight: number
  setControlsHeight: (controlsHeight: number) => void
  setTime: (time: number) => void
  setPlaying: (playing: boolean) => void
  setView: (view: BattleView) => void
  reset: () => void
}

export const useBattle = create<BattleState>()((set) => ({
  time: 0,
  playing: false,
  view: 'tactical',
  controlsHeight: 0,
  setControlsHeight: (controlsHeight) => set({ controlsHeight }),
  setTime: (time) => set({ time }),
  setPlaying: (playing) => set({ playing }),
  setView: (view) => set({ view }),
  reset: () => set({ time: 0, playing: false, view: 'tactical' }),
}))
