import List from '@/src/components/List'
import TaskCard from '@/src/components/TaskCard'
import { getTasks } from '@/src/utils/processUtils'

import styles from './page.module.scss'

export default async function TasksPage() {
  const tasks = await getData()

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Tasks</h1>
        <div className={styles.tools}></div>
      </div>
      <div className={styles.body}>
        <List className={styles.list}>
          {tasks?.map((task, idx) => {
            return <TaskCard task={task} className={styles.card} key={idx} />
          })}
        </List>
      </div>
    </div>
  )
}

async function getData() {
  return await getTasks()
}
