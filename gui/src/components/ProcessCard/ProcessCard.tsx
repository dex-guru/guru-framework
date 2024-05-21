import Link from 'next/link'

import { FC } from 'react'

import clsx from 'clsx'

import { ProcessDefinition } from '@/app/processes/types'

import InstanceStarter from '../InstanceStarter'

import styles from './ProcessCard.module.scss'

export const ProcessCard: FC<{
  process: ProcessDefinition
  className?: string
}> = ({ process, className }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <Link href={`/processes/${process.id}`} className={styles.title}>
        {process.name}
      </Link>
      <div className={styles.footer}>
        <div className={styles.entryInstances}>
          {process.instanceCount || 'No'} instance
          {!process?.instanceCount || process?.instanceCount > 1 ? 's' : ''}
        </div>
        <div className={styles.actions}>
          <InstanceStarter process={process} />
        </div>
      </div>
    </div>
  )
}
