import Link from 'next/link'

import InstanceRemover from '@/src/components/InstanceRemover'
import InstanceStarter from '@/src/components/InstanceStarter'
import Panel from '@/src/components/Panel'
import Viewer from '@/src/components/Viewer'
import { getDefinition, getInstances } from '@/src/utils/processUtils'

import styles from './page.module.scss'

export const dynamic = 'force-dynamic'

export default async function InstancesPage({ params: { id } }: { params: { id: string } }) {
  const { process, instances } = await getData(id)

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Process</h1>
        <div className={styles.tabs}>
          <ul className={styles.tabsList}></ul>
        </div>
        <div className={styles.tools}></div>
      </div>
      <div className={styles.body}>
        <aside className={styles.aside}>
          <Panel title="Properties">
            <div className={styles.props}>
              <table className={styles.propsTable}>
                <tbody className={styles.propsTBody}>
                  {Object.entries(process).map(([key, value]) => {
                    return (
                      <tr className={styles.propsTR} key={key}>
                        <th className={styles.propsTH}>{key}</th>
                        <td className={styles.propsTD}>{value}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel title="Instances" tools={<InstanceStarter process={process} />}>
            <div className={styles.instances}>
              <table className={styles.instancesTable}>
                <tbody className={styles.instancesTBody}>
                  {instances.map((instance) => {
                    return (
                      <tr className={styles.instancesTBody} key={instance.id}>
                        <th className={styles.instancesTH}>
                          <Link href={`/processes/${process.id}/${instance.id}`}>
                            {instance.id}
                          </Link>
                        </th>
                        <td className={styles.instancesTD}>
                          {instance.ended ? 'Ended' : 'In progress'}{' '}
                        </td>
                        <td className={styles.instancesTD}>
                          {instance.suspended ? 'Suspended' : 'Active'}
                        </td>
                        <td className={styles.instancesTD}>
                          <InstanceRemover instance={instance} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Panel>
        </aside>

        <main className={styles.content}>
          <Viewer process={process.id} className={styles.viewer} />
        </main>
      </div>
    </div>
  )
}

async function getData(id: string) {
  return {
    process: await getDefinition(id),
    instances: await getInstances(id),
  }
}
