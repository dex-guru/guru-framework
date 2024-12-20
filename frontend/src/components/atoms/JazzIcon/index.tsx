import * as React from 'react'
import { FC } from 'react'

import MersenneTwister from 'mersenne-twister'

import { colorRotate, colors } from './utils'

// constants
const shapeCount = 4
const svgns = 'http://www.w3.org/2000/svg'
const wobble = 30

type JazzIconProps = {
  size?: number
  seed?: number
  style?: object
  className?: string
}

type Colors = Array<string>

const JazzIcon: FC<JazzIconProps> = ({ size = 100, seed, style = {}, className }) => {
  const generator = new MersenneTwister(seed)

  const genColor = (colors: Colors): string => {
    generator.random() // purposefully call the generator once, before using it again on the next line
    const idx = Math.floor(colors.length * generator.random())
    const color = colors.splice(idx, 1)[0]
    return color
  }

  const hueShift = (colors: Colors, generator: MersenneTwister): Array<string> => {
    const amount = generator.random() * 30 - wobble / 2
    const rotate = (hex: string) => colorRotate(hex, amount)
    return colors.map(rotate)
  }

  const genShape = (remainingColors: Colors, diameter: number, i: number, total: number) => {
    const center = diameter / 2
    const firstRot = generator.random()
    const angle = Math.PI * 2 * firstRot
    const velocity = (diameter / total) * generator.random() + (i * diameter) / total
    const tx = Math.cos(angle) * velocity
    const ty = Math.sin(angle) * velocity
    const translate = 'translate(' + tx + ' ' + ty + ')'

    // Third random is a shape rotation on top of all of that.
    const secondRot = generator.random()
    const rot = firstRot * 360 + secondRot * 180
    const rotate = 'rotate(' + rot.toFixed(1) + ' ' + center + ' ' + center + ')'
    const transform = translate + ' ' + rotate
    const fill = genColor(remainingColors)

    return (
      <rect
        key={i}
        x="0"
        y="0"
        rx="0"
        ry="0"
        height={diameter}
        width={diameter}
        transform={transform}
        fill={fill} // todo: make prop
      />
    )
  }

  const remainingColors = hueShift(colors.slice(), generator)
  const shapesArr = Array(shapeCount).fill(undefined)

  return (
    <svg
      xmlns={svgns}
      viewBox={`0 0 ${size} ${size}`}
      width={size}
      height={size}
      className={className}
      style={{ ...style, background: genColor(remainingColors) }}>
      {shapesArr.map((s, i) => genShape(remainingColors, size, i, shapeCount - 1))}
    </svg>
  )
}

export default JazzIcon
