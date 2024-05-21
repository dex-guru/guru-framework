'use client'

import { ChangeEventHandler, FC, MouseEventHandler, useEffect, useRef } from 'react'

import BpmnModeler from 'camunda-bpmn-js/lib/camunda-platform/Modeler'
import clsx from 'clsx'
import { FaCheckToSlot, FaDownload, FaFile, FaRegFolderOpen } from 'react-icons/fa6'

import Modeler from '@/src/components/Modeler'

import Button from '../Button'

import styles from './ModelerPage.module.scss'
import Canvas from '@node_modules/diagram-js/lib/core/Canvas'

const ModelerPage: FC<{ className?: string }> = ({ className }) => {
  const refFile = useRef<HTMLInputElement>(null)
  const refModeler = useRef<BpmnModeler | null>(null)

  useEffect(() => {
    //
  }, [])

  const handleOpenFile: ChangeEventHandler<HTMLInputElement> = (e) => {
    e.preventDefault()

    if (!e.target?.files?.length) {
      return
    }

    const reader = new FileReader()
    reader.onload = async (e) => {
      const xml = e.target?.result
      await refModeler.current?.importXML(xml?.toString() || '')
      const canvas = refModeler.current?.get<Canvas>('canvas')
      canvas?.zoom('fit-viewport')
    }

    reader.readAsText(e.target.files[0])
  }

  const handleOpenClick: MouseEventHandler = () => {
    refFile.current?.click()
  }

  const handleDownload = () => {
    refModeler.current?.saveXML().then((xmlResult) => {
      const element = document.createElement('a')
      const file = new Blob([xmlResult.xml || ''], {
        type: 'application/xml',
      })
      element.href = URL.createObjectURL(file)
      element.download = 'model.bpmn'
      document.body.appendChild(element) // Required for this to work in FireFox
      element.click()
    })
  }

  const handleInit = (modeler: BpmnModeler | null) => {
    refModeler.current = modeler
  }

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <h1 className={styles.title}>Modeler</h1>
        <div className={styles.tools}>
          <input
            ref={refFile}
            type="file"
            onChange={handleOpenFile}
            accept=".bpmn, .xml"
            className={styles.file}
          />
          <Button
            icon={<FaFile />}
            onClick={() => {
              refModeler.current?.createDiagram()
            }}
            className={styles.toolsAction}
          />

          <Button
            icon={<FaRegFolderOpen />}
            onClick={handleOpenClick}
            className={styles.toolsAction}
          />

          <Button icon={<FaDownload />} onClick={handleDownload} className={styles.toolsAction} />

          <Button
            icon={<FaCheckToSlot />}
            className={styles.toolsAction}
            onClick={() => {
              if (typeof window === 'undefined') {
                return
              }

              const name = window?.prompt('Enter deployment name', 'random name') || ''

              if (!name?.trim()) {
                return
              }

              refModeler.current?.saveXML().then(async (xmlResult) => {
                if (!xmlResult.xml) {
                  return
                }

                const formData = new FormData()
                formData.append('process.bpmn', new Blob([xmlResult.xml]))
                formData.append('deployment-name', name)

                const res = await fetch('api/engine/deployment/create', {
                  method: 'POST',
                  body: formData,
                })

                if (!res.ok) {
                  console.log(`Failed to deploy data: ${res.statusText} [${res.status}]`)
                }
              })
            }}
          />
        </div>
      </div>
      <div className={styles.body}>
        <Modeler onInit={handleInit} />
      </div>
    </div>
  )
}

export default ModelerPage
