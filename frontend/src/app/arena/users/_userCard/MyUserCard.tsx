'use client'

import { useSession } from 'next-auth/react'

import { useMyTopUser } from '@/services/flow/hooks/flow'
import { components } from '@/services/flow/schema'

import { UserCard } from './UserCard'

type UserCardProps = {
  user: components['schemas']['UsersLeaderBoardRest'] | null
}

export function MyUserCard({ user }: UserCardProps) {
  const { data: session } = useSession()
  const { data: myUser } = useMyTopUser(session?.user.web3_wallets[0].wallet_address)
  if (!user || !myUser) {
    return null
  }
  if (myUser) {
    return <UserCard user={myUser} />
  }
  return <UserCard user={user} />
}
