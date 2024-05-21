'use client'

import { FC, useEffect, useRef } from 'react'

import BpmnViewer from 'bpmn-js/lib/Viewer'
import clsx from 'clsx'

import { fetchEngine } from '@/src/utils/processUtils'

import styles from './Viewer.module.scss'

import 'camunda-bpmn-js/dist/assets/camunda-platform-viewer.css'
import Canvas from '@node_modules/diagram-js/lib/core/Canvas'

export const Viewer: FC<{ process: string; className?: string }> = ({ process, className }) => {
  const refCanvas = useRef<HTMLDivElement>(null)
  const refViewer = useRef<BpmnViewer | null>(null)

  useEffect(() => {
    if (!refCanvas.current || refViewer.current) {
      return
    }

    const viewer = new BpmnViewer({
      container: refCanvas.current || '',
    })
    refViewer.current = viewer

    const getXml = async () => {
      try {
        const res = await fetchEngine(`process-definition/${process}/xml`)

        if (!res.ok) {
          return
        }

        const { bpmn20Xml } = await res.json()
        await viewer?.importXML(bpmn20Xml)
        const canvas = refViewer.current?.get<Canvas>('canvas')
        canvas?.zoom('fit-viewport')
      } catch (e) {
        console.error(e)
      }
    }

    getXml()
  }, [process, refCanvas])

  return <div className={clsx(styles.container, className)} ref={refCanvas} />
}
