'use client'

import { FC, useCallback } from 'react'

import { FaPlay } from 'react-icons/fa6'

import { ProcessDefinition } from '@/app/processes/types'
import { startNewInstance } from '@/src/utils/processUtils'

import Button from '../Button'

export const InstanceStarter: FC<{ process: ProcessDefinition }> = ({ process }) => {
  const handleNewInstance = useCallback(() => startNewInstance(process), [process])

  return <Button icon={<FaPlay />} caption="New Instance" onClick={handleNewInstance} />
}
