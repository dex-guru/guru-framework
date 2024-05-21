export type ProcessInstance = {
  links: []
  id: string
  definitionId: string
  businessKey: string | null
  caseInstanceId: string | null
  ended: boolean
  suspended: boolean
  tenantId: string | null
}

export type ProcessDefinition = {
  id: string
  key: string
  category: string
  description: string | null
  name: string
  version: number
  resource: string
  deploymentId: string
  diagram: string | null
  suspended: boolean
  tenantId: string | null
  versionTag: string | null
  historyTimeToLive: number
  startableInTasklist: boolean
  instanceCount?: number
}

export type ProcessVariable = {
  value: unknown
  type: string
  valueInfo: Record<string, string>
}

export type ProcessVariables = Record<string, ProcessVariable>
