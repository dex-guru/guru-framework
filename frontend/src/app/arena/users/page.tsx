import { cookies } from 'next/headers'

import auth from '@/auth'
import { Caption } from '@/components/ui'
import { FlowClientObject } from '@/services/flow'

import { MyUserCard } from './_userCard/MyUserCard'
import { UserCard } from './_userCard/UserCard'

import styles from './_assets/page.module.scss'

export default async function PageUsers() {
  const cookieStore = cookies()
  console.log('cookieStore on /users page', cookieStore)
  const session = await auth()

  const users = await FlowClientObject.leaderboard.users.list()
  const myUser = await FlowClientObject.leaderboard.users.get(
    session?.user.web3_wallets[0].wallet_address
  )

  return (
    <div className={styles.container}>
      <Caption size="sm" className={styles.title} strong>
        You
      </Caption>
      <MyUserCard user={myUser} />
      <Caption size="sm" className={styles.title}>
        Top 10
      </Caption>
      <div className={styles.users}>
        {users.map((user) => (
          <UserCard key={user.wallet_address} user={user} />
        ))}
      </div>
    </div>
  )
}
