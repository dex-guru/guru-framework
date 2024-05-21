import { FC } from 'react'

import clsx from 'clsx'

import JazzIcon from './JazzIcon'
import { AvatarProps } from './types'
import { jsNumberForAddress } from './utils'

import styles from './Avatar.module.scss'

const Avatar: FC<AvatarProps> = ({ address, letters, className, type = 'smooth' }) => {
  return (
    <div className={clsx(styles.container, styles[type], className)} data-letters={letters}>
      {!!address && (
        <JazzIcon size={32} seed={jsNumberForAddress(address)} className={styles.icon} />
      )}
    </div>
  )
}

export default Avatar
