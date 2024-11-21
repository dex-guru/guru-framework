'use client'

import { CanvasHTMLAttributes, FC } from 'react'

import { DotLottieReact } from '@lottiefiles/dotlottie-react'
import clsx from 'clsx'

import styles from './Burn.module.scss'

type BurnProps = CanvasHTMLAttributes<HTMLCanvasElement>

export const Burn: FC<BurnProps> = (props) => {
  return (
    <DotLottieReact
      src="/assets/lottie/burn.lottie"
      loop
      autoplay
      {...props}
      className={clsx(styles.container, props.className)}
    />
  )
}
