import type { SIWECreateMessageArgs, SIWESession, SIWEVerifyMessageArgs } from '@reown/appkit-siwe'
import { createSIWEConfig, formatMessage } from '@reown/appkit-siwe'
import { mainnet } from '@reown/appkit/networks'
import { retrieveLaunchParams } from '@telegram-apps/bridge'
import { getCsrfToken, getSession, signIn, signOut } from 'next-auth/react'

import { tGuru } from './wagmi'

export const siweConfig = createSIWEConfig({
  getMessageParams: async () => ({
    domain: typeof window !== 'undefined' ? window.location.host : '',
    uri: typeof window !== 'undefined' ? window.location.origin : '',
    chains: [mainnet.id, tGuru.id],
    statement: 'Please sign with your account',
  }),
  createMessage: ({ address, ...args }: SIWECreateMessageArgs) => formatMessage(args, address),
  getNonce: async () => {
    const nonce = await getCsrfToken()
    if (!nonce) {
      throw new Error('Failed to get nonce!')
    }

    return nonce
  },
  getSession: async () => {
    const session = await getSession()
    if (!session) {
      throw new Error('Failed to get session!')
    }

    const { address, chainId } = session as unknown as SIWESession

    return { address, chainId }
  },
  verifyMessage: async ({ message, signature }: SIWEVerifyMessageArgs) => {
    try {
      const launchParams = retrieveLaunchParams()
      console.log(launchParams)
      if (launchParams?.initData?.user) {
        const success = await signIn('credentials', {
          message,
          redirect: false,
          signature,
          telegram_user: JSON.stringify(launchParams.initData.user),
        })

        return Boolean(success?.ok)
      }
      return false
    } catch (error) {
      console.error(error)
      return false
    }
  },
  signOut: async () => {
    try {
      await signOut({
        redirect: false,
      })

      return true
    } catch (error) {
      console.error(error)

      return false
    }
  },
})
