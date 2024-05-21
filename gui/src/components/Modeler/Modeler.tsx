'use client'

import { FC, useEffect, useRef } from 'react'

import BpmnModeler from 'camunda-bpmn-js/lib/camunda-platform/Modeler'

import styles from './Modeler.module.scss'

import 'camunda-bpmn-js/dist/assets/camunda-platform-modeler.css'

export const Modeler: FC<{ onInit: (modeler: BpmnModeler) => void }> = ({ onInit }) => {
  const refCanvas = useRef<HTMLDivElement>(null)
  const refProps = useRef<HTMLDivElement>(null)
  const refModeler = useRef<BpmnModeler | null>(null)

  useEffect(() => {
    if (!refCanvas.current || refModeler.current) {
      return
    }

    const modeler = new BpmnModeler({
      container: refCanvas.current,
      propertiesPanel: {
        parent: refProps.current,
      },
    })

    modeler?.createDiagram()
    refModeler.current = modeler

    onInit?.(modeler)
  }, [onInit, refCanvas])

  return (
    <div className={styles.container}>
      <div className={styles.canvas} ref={refCanvas}></div>
      <div className={styles.properties} ref={refProps}></div>
    </div>
  )
}
