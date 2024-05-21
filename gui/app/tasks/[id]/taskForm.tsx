'use client'

import { FC } from 'react'

import { AbiFunction } from 'abitype'
import { useForm } from 'react-hook-form'
import { useAccount, useEstimateGas, useSendTransaction, useWaitForTransactionReceipt } from 'wagmi'

import Button from '@/src/components/Button'

import styles from './page.module.scss'

type TaskFormProps = {
  vars: unknown
  abi: AbiFunction
}

export const TaskForm: FC<TaskFormProps> = ({ abi }) => {
  const { address } = useAccount()

  const { register, handleSubmit, formState, watch } = useForm()
  const to = watch('_to')
  const value = watch('_value')

  const { data: gas } = useEstimateGas({
    to: to,
    value: value,
    account: address,
  })

  const { data: hash, sendTransaction } = useSendTransaction()

  const { isLoading } = useWaitForTransactionReceipt({
    hash,
  })

  if (!address) {
    return <w3m-button />
  }

  return (
    <form
      className={styles.form}
      onSubmit={handleSubmit(() => {
        if (!sendTransaction) {
          throw new Error('sendTransaction is not defined')
        }
        sendTransaction({
          gas: gas || undefined,
          to: to,
          value: value,
        })
      })}>
      {abi.inputs.map((abiParam, idx) => {
        return (
          <label key={idx} className={styles.formField}>
            <strong className={styles.formFieldTitle}>{abiParam.name || `param ${idx}`}</strong>
            <input
              className={styles.formFieldInput}
              {...register(abiParam.name || `param ${idx}`, {
                required: true,
              })}
            />
            {formState.errors.exampleRequired && <span>This field is required</span>}
          </label>
        )
      })}

      <Button
        caption={isLoading ? 'Sending...' : 'Send'}
        buttonType="submit"
        disabled={isLoading || !sendTransaction || !to || !value}
      />
    </form>
  )
}
