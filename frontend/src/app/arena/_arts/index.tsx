'use client'

import { Meme } from '@/components/composed/Meme/Meme'
import { Caption } from '@/components/ui/Caption'
import { components } from '@/services/flow/schema'

import styles from '../_assets/page.module.scss'

interface LeaderboardArtsProps {
  arts: components['schemas']['ArtLeaderBoardRest'][]
  artsFinances: components['schemas']['ArtFinanceRest'][]
}

export default function PageArena({ arts, artsFinances }: LeaderboardArtsProps) {
  return (
    <>
      <Caption className={styles.memes__title}>All Memes</Caption>
      <ul className={styles.memes__list}>
        {arts.map((art, index: number) => {
          const artRest = art.art as components['schemas']['ArtRest']
          const finances = artsFinances?.find((x) => x.token_address === art.token_address)
          return (
            <li key={index}>
              <Meme
                artId={artRest.id}
                rank={index + 1}
                title={art.name}
                participants={art.participants_count}
                imageSrc={artRest?.img_picture ?? ''}
                hasFinances={!!finances?.total_supply}
                description={artRest?.description ?? ''}
                locked={finances?.guru_balance}
                ratio={
                  finances && finances.total_supply > 0
                    ? [
                        finances.burn_total_supply / finances.total_supply,
                        finances.mint_total_supply / finances.total_supply,
                      ]
                    : undefined
                }
              />
            </li>
          )
        })}
      </ul>
    </>
  )
}
