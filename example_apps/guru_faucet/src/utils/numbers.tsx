import { ReactNode } from 'react'

import Value from '@/components/Value'

import styles from './numbers.module.scss'

export type FormatNumberOptions = {
  leaveTrailingZeroes?: boolean
} & Intl.NumberFormatOptions

export const getFirstSignificantDecimalIndex = (value: number) =>
  (`${value.toLocaleString('en-US', { minimumFractionDigits: 18 })}`
    .split('.')[1]
    ?.match(/^(0+)[^0]/)?.[1].length || 1) + 1

export const formatNumber = (
  value?: bigint | string | number | null,
  options: FormatNumberOptions = {
    leaveTrailingZeroes: false,
  }
): string => {
  if (typeof value === 'undefined' || value === null) {
    return 'N/A'
  }

  const { leaveTrailingZeroes, ...props } = options

  const valueNumber = Number(value)

  const result = Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits:
      value && Math.abs(valueNumber) < 0.01
        ? Math.max(7, getFirstSignificantDecimalIndex(valueNumber)) + 1
        : 2,
    ...props,
  }).format(valueNumber)

  return !leaveTrailingZeroes ? result.replace(/\.0+$/, '') : result
}

export const renderFormatNumber = (
  value?: number | null,
  props: {
    infinityLimit?: number
    options?: FormatNumberOptions
    prefix?: ReactNode
    suffix?: ReactNode
    delta?: number
  } = { options: { leaveTrailingZeroes: false } }
) => {
  if (typeof value === 'undefined' || value === null) {
    return <span className={styles.sign}>N/A</span>
  }

  if (value >= (props.infinityLimit ?? 10 ** 12)) {
    return (
      <span
        data-tooltip-content={formatNumber(value, {
          notation: 'standard',
          leaveTrailingZeroes: props?.options?.leaveTrailingZeroes,
        })}
        data-tooltip-id="app-tooltip">
        ∞
      </span>
    )
  }

  return (
    <Value
      value={formatNumber(value, props?.options)}
      prefix={props?.prefix}
      suffix={props?.suffix}
      delta={props?.delta}
    />
  )
}
