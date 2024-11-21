import Image from 'next/image'

import { Caption, Tab } from '@/components/ui'
import leaderboardIcon from '@/images/icons/leaderboard-title.png'

import styles from './_assets/layout.module.scss'

export default function ArenaLayout({ children }: React.PropsWithChildren) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Caption variant="header" size="lg" strong>
          Arena
        </Caption>
      </div>
      <div className={styles.illustration}>
        <Image priority={true} src={leaderboardIcon} alt="Arena" fill={true} />
      </div>
      <div className={styles.body}>
        <div className={styles.tabs}>
          <Tab href="/arena/users" exact={true}>
            Users
          </Tab>
          <Tab href="/arena" exact={true}>
            Memes
          </Tab>
        </div>
        {children}
      </div>
    </div>
  )
}
