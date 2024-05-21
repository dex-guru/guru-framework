import Link from 'next/link'

import React, { ReactNode, Ref, forwardRef } from 'react'

import clsx from 'clsx'
import { UrlObject } from 'url'

import styles from './Button.module.scss'

export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
export type ButtonType = 'default' | 'primary' | 'secondary' | 'tertiary' | 'link' | 'action'

export type ButtonProps = {
  caption?: ReactNode
  icon?: ReactNode
  indicator?: ReactNode
  counter?: string
  className?: string
  isActive?: boolean
  isDisabled?: boolean
  isHidden?: boolean
  size?: ButtonSize
  type?: ButtonType
  buttonType?: 'button' | 'submit' | 'reset'
  isAccent?: boolean
  href?: string | UrlObject
}

export const Button = forwardRef(function Button(
  {
    caption,
    icon,
    indicator,
    counter,
    className,
    isActive,
    isDisabled,
    isHidden,
    href,
    children,
    type = 'default',
    size = 'md',
    buttonType = 'button',
    isAccent,
    ...rest
  }: Omit<React.HTMLProps<HTMLAnchorElement>, 'href' | 'size'> & ButtonProps,
  ref
) {
  const classProp = clsx(
    styles.container,
    {
      [styles[type]]: !!type,
      [styles[size]]: !!type,
      [styles.accent]: isAccent,
      [styles.active]: isActive,
      [styles.disabled]: isDisabled,
      [styles.hidden]: isHidden,
    },
    className
  )

  const content = (
    <>
      {!!icon && <span className={styles.icon}>{icon}</span>}
      {(caption || children) && <span className={styles.caption}>{caption || children}</span>}
      {!!indicator && <span className={styles.indicator}>{indicator}</span>}
      {!!counter && <span className={styles.counter}>{counter}</span>}
    </>
  )

  const props = {
    className: classProp,
    disabled: isDisabled,
    hidden: isHidden,

    ...rest,
  }

  if (href) {
    return (
      <Link {...props} href={href} ref={ref as Ref<HTMLAnchorElement>}>
        {content}
      </Link>
    )
  }

  return React.createElement(
    'button',
    {
      ...props,
      type: buttonType,
      ref: ref as Ref<HTMLButtonElement>,
    },
    content
  )
})
