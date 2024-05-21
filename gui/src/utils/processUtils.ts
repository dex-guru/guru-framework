import { ProcessDefinition, ProcessInstance, ProcessVariables } from '@/app/processes/types'
import { ProcessTask, TaskVariables } from '@/app/tasks/types'

export const fetchEngine = async (
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> => {
  const hostUrl =
    typeof window === 'undefined' ? process.env.CAMUNDA_URL : '/dashboard/api/engine'

  return fetch(`${hostUrl}/${input}`, { ...init, cache: 'no-cache' })
}

export const getInstances = async (id?: string): Promise<ProcessInstance[]> => {
  const res = await fetchEngine(`process-instance${id ? `?processDefinitionId=${id}` : ''}`)

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to fetch data: ${res.statusText} [${res.status}]`)
  }

  const instances: ProcessInstance[] = await res.json()

  return instances
}

export const getDefinition = async (id: string): Promise<ProcessDefinition> => {
  const res = await fetchEngine(`process-definition?processDefinitionId=${id}`)

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to fetch data: ${res.statusText} [${res.status}]`)
  }

  const processes: ProcessDefinition[] = await res.json()

  return processes[0]
}

export const getInstance = async (id: string): Promise<ProcessInstance> => {
  const res = await fetchEngine(`process-instance/${id}`)

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to fetch data: ${res.statusText} [${res.status}]`)
  }

  const instance: ProcessInstance = await res.json()

  return instance
}

export const getVariables = async (id: string): Promise<ProcessVariables> => {
  const res = await fetchEngine(`process-instance/${id}/variables`)

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to fetch data: ${res.statusText} [${res.status}]`)
  }

  const vars: ProcessVariables = await res.json()

  return vars
}

export const getDefinitions = async (): Promise<ProcessDefinition[]> => {
  const res = await fetchEngine('process-definition')

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to fetch data: ${res.statusText} [${res.status}]`)
  }

  const processes: ProcessDefinition[] = await res.json()

  await Promise.all(
    processes.map(async (process, idx) => {
      processes[idx].instanceCount = await getInstanceCount(process.id)
    })
  )

  return processes
}

export const getInstanceCount = async (id: string): Promise<number> => {
  const res = await fetchEngine(`process-instance/count?processDefinitionId=${id}`)

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to fetch data: ${res.statusText} [${res.status}]`)
  }

  const { count } = await res.json()

  return count
}

export const getTasks = async (
  id?: string | null,
  definitionId?: string | null,
  instanceId?: string | null
): Promise<ProcessTask[]> => {
  const query = []

  if (id) {
    query.push(`id=${id}`)
  }

  if (definitionId) {
    query.push(`processDefinitionId=${definitionId}`)
  }

  if (instanceId) {
    query.push(`processInstanceId=${instanceId}`)
  }

  const res = await fetchEngine(`task?${query.join('&')}`)

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to fetch data: ${res.statusText} [${res.status}]`)
  }

  const tasks: ProcessTask[] = await res.json()
  return tasks
}

export const getTaskVariables = async (taskId: string): Promise<TaskVariables> => {
  const res = await fetchEngine(`task/${taskId}/form-variables`)

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to fetch task variables: ${res.statusText} [${res.status}]`)
  }

  const vars: TaskVariables = await res.json()
  return vars
}

export const setTaskVariables = async (
  taskId: string,
  variables: TaskVariables
): Promise<number> => {
  const body = {
    modifications: variables,
  }
  const res = await fetchEngine(`task/${taskId}/variables`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to set variables: ${res.statusText} [${res.status}]`)
  }

  return res.status
}

export const completeTask = async (taskId: string, variables: TaskVariables): Promise<number> => {
  const body = {
    variables,
  }
  const res = await fetchEngine(`task/${taskId}/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error(`Failed to complete task with variables: ${res.statusText} [${res.status}]`)
  }

  return res.status
}

export const startNewInstance = async (process: ProcessDefinition) => {
  const res = await fetchEngine(`process-definition/key/${process.key}/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  })

  if (!res.ok) {
    return
  }

  const resBody = await res.json()
  console.log(resBody)
}
