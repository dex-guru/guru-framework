'use server'

import withFetchRetry, { RequestInitRetryParams } from 'fetch-retry'
import get from 'lodash/get'
import { UrlObject, format } from 'url'

export type AppFetchProps = RequestInit & {
  url: string | UrlObject
  data?: Record<string, unknown>
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  headers?: HeadersInit
  timeout?: number
  isLog?: boolean
} & RequestInitRetryParams<typeof fetch>

const fetchRetry = withFetchRetry(fetch)

export const appFetch = async ({
  url,
  method = 'GET',
  data,
  timeout = 0,
  ...rest
}: AppFetchProps) => {
  const start = performance.now()

  const urlString = format(url)
  const body = data ? JSON.stringify(data) : undefined

  return fetchRetry(urlString, {
    method,
    body,
    signal: timeout ? AbortSignal.timeout(timeout) : undefined,
    mode: 'no-cors',
    next: {
      revalidate: rest.cache ? undefined : 1 * 60,
      tags: ['all', 'fetch', urlString],
    },
    ...rest,
  })
    .then((res) => {
      const time = performance.now() - start
      if (res.ok) {
        return res
      } else {
        const resData = {
          url: urlString,
          method,
          performance: time,
          params: {
            body: data,
            status: res.status,
            statusText: res.statusText,
          },
        }

        throw new Error(JSON.stringify(resData))
      }
    })
    .catch((error) => {
      console.log(error)

      if (error instanceof Error) {
        throw error
      }
      throw new Error(JSON.stringify(error))
    })
}

export const appFetchJSON = async ({
  section,
  ...props
}: AppFetchProps & {
  section?: string | number | symbol | [string | number | symbol]
}) => {
  const json = await appFetch(props).then((res) => res.json())
  return section ? get(json ?? {}, section) : json
}
