
export type ProcessTask = {
  id: string
  name: string
  assignee: string
  created: string
  due: string
  'followUp:': string
  'lastUpdated:': string
  delegationState: string
  description: string
  executionId: string
  owner: string
  parentTaskId: string
  priority: number
  processDefinitionId: string
  processInstanceId: string
  caseDefinitionId: string
  caseInstanceId: string
  caseExecutionId: string
  taskDefinitionKey: string
  suspended: false
  formKey: string
  tenantId: string
}

export type TaskVariables = {
  [variable: string]: {
    value: unknown
    type: string
    valueInfo: {
      objectTypeName?: string
      serializationDataFormat?: string
    }
  }
}
