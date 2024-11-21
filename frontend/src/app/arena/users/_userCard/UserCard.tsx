import JazzIcon from '@/components/atoms/JazzIcon'
import { jsNumberForAddress } from '@/components/atoms/JazzIcon/utils'
import { Show } from '@/components/ui'
import { Burns } from '@/components/ui/Burns'
import { Caption } from '@/components/ui/Caption'
import { Icon } from '@/components/ui/Icon'
import { Rank } from '@/components/ui/Rank'
import { components } from '@/services/flow/schema'
import { formatNumber } from '@/utils/numbers'
import { getShortAddress } from '@/utils/strings'

import styles from './UserCard.module.scss'

type UserCardProps = {
  user: components['schemas']['UsersLeaderBoardRest']
}

export function UserCard({ user }: UserCardProps) {
  const address = user.wallet_address

  return (
    <div className={styles.container}>
      <div className={styles.illustration}>
        <Show if={address}>
          <JazzIcon size={48} seed={jsNumberForAddress(address)} className={styles.icon} />
        </Show>
      </div>
      <div className={styles.body}>
        <div className={styles.title}>
          <Caption size="sm">{getShortAddress(address) ?? 'Anonymous'}</Caption>
          <Icon iconName="star" />
        </div>
        <div className={styles.stats}>
          <div className={styles.stat}>
            <Burns size="xs">{formatNumber(user.total_locked ?? 0, { notation: 'compact' })}</Burns>
          </div>
          <div className={styles.stat}>
            <Caption size="xs">{`${user.token_addresses.length} Memes`}</Caption>
          </div>
          <div className={styles.stat}>
            <Caption size="xs">{`${formatNumber(user.total_burns ?? 0, { notation: 'compact' })} Burned / ${formatNumber(user.total_mints ?? 0, { notation: 'compact' })} Mint`}</Caption>
          </div>
        </div>
      </div>
      <div className={styles.footer}>
        <Rank rank={user.rank} />
      </div>
    </div>
  )
}
