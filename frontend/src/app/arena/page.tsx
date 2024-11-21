import { unstable_noStore as noStore } from 'next/cache'

import { FlowClientObject } from '@/services/flow'

import LeaderBoardArts from './_arts'

export default async function Index() {
  noStore()
  const arts = await FlowClientObject.leaderboard.arts.list()
  const artsFinances = await FlowClientObject.arts.finances(
    arts?.length
      ? (arts.filter((x) => !!x.token_address).map((x) => x.token_address) as string[])
      : undefined
  )

  if (!arts || !artsFinances) {
    return <div>Error loading memes or no data available</div>
  }

  return <LeaderBoardArts arts={arts} artsFinances={artsFinances} />
}
