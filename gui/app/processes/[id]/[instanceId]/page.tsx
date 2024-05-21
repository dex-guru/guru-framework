import Link from 'next/link'

import List from '@/src/components/List'
import Panel from '@/src/components/Panel'
import Viewer from '@/src/components/Viewer'
import { getInstance, getTasks, getVariables } from '@/src/utils/processUtils'

import styles from './page.module.scss'

export const dynamic = 'force-dynamic'

export default async function InstancePage({
  params: { instanceId },
}: {
  params: { instanceId: string }
}) {
  const { instance, variables, tasks } = await getData(instanceId)

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Instance</h1>
        <div className={styles.tabs}>
          <ul className={styles.tabsList}></ul>
        </div>
        <div className={styles.tools}></div>
      </div>
      <div className={styles.body}>
        <aside className={styles.aside}>
          <Panel title="Properties">
            <table className={styles.propsTable}>
              <tbody className={styles.propsTBody}>
                {Object.entries(instance).map(([key, value]) => {
                  return (
                    <tr className={styles.propsTR} key={key}>
                      <th className={styles.propsTH}>{key}</th>
                      <td className={styles.propsTD}>{value}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </Panel>
          <Panel title="Tasks">
            <List className={styles.list}>
              {tasks?.map((task, idx) => (
                <Link key={idx} href={`/tasks/${task.id}`}>
                  {task.id}
                  <style>{`[data-element-id="${task.taskDefinitionKey}"] {outline-color: red; outline-style: auto }`}</style>
                </Link>
              ))}
            </List>
          </Panel>
        </aside>
        <main className={styles.content}>
          <Viewer process={instance.definitionId} className={styles.viewer} />
          <div className={styles.variables}>
            <table className={styles.variablesTable}>
              <tbody className={styles.variablesTBody}>
                {Object.entries(variables).map(([varKey, varValue]) => {
                  return (
                    <tr className={styles.variablesTBody} key={varKey}>
                      <th className={styles.variablesTH}>{varKey}</th>
                      <td className={styles.variablesTD}>{varValue.type}</td>
                      <td className={styles.variablesTD}>{JSON.stringify(varValue.value)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  )
}

async function getData(id: string) {
  return {
    instance: await getInstance(id),
    variables: await getVariables(id),
    tasks: await getTasks(null, null, id),
  }
}
