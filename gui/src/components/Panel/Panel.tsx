import { FC, ReactNode } from 'react'

import clsx from 'clsx'

import styles from './Panel.module.scss'

type PanelProps = {
  className?: string
  title: ReactNode
  tools?: ReactNode | ReactNode[]
  children?: ReactNode | ReactNode[]
}

export const Panel: FC<PanelProps> = ({ title, tools, className, children }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
        {!!tools && <div className={styles.tools}>{tools}</div>}
      </div>
      <div className={styles.body}>{children}</div>
    </div>
  )
}
