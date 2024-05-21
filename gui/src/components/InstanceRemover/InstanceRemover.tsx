'use client'

import { FC } from 'react'

import { FaTrash } from 'react-icons/fa6'

import { ProcessInstance } from '@/app/processes/types'
import { fetchEngine } from '@/src/utils/processUtils'

import Button from '../Button'

export const InstanceRemover: FC<{ instance: ProcessInstance }> = ({ instance }) => {
  const onDelete = async () => {
    const res = await fetchEngine(
      `process-instance/${instance.id}?skipCustomListeners=true&skipIoMappings=true`,
      {
        method: 'DELETE',
      }
    )

    if (!res.ok) {
      const json = await res.json()
      if (json?.body?.message) {
        alert(json?.body?.message)
      }

      console.log(`Failed to deploy data: ${res.statusText} [${res.status}]`)
      return
    }

    if (window === undefined) {
      return
    }

    window.location.reload()
  }

  return <Button icon={<FaTrash />} caption="Delete" onClick={onDelete} />
}
