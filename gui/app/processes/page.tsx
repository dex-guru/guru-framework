import List from '@/src/components/List'
import ProcessCard from '@/src/components/ProcessCard'
import { getDefinitions } from '@/src/utils/processUtils'

import styles from './page.module.scss'

export default async function ProjectsPage() {
  const processes = await getData()

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Processes</h1>
        <div className={styles.tools}></div>
      </div>
      <div className={styles.body}>
        <List className={styles.list}>
          {processes?.map((process) => {
            return <ProcessCard process={process} className={styles.card} key={process.key} />
          })}
        </List>
      </div>
    </div>
  )
}

async function getData() {
  return await getDefinitions()
}
