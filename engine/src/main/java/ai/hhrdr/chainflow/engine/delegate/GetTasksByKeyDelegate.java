package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.TaskService;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.camunda.bpm.engine.task.Task;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.text.SimpleDateFormat;
import java.util.*;

public class GetTasksByKeyDelegate implements JavaDelegate {

    private static final Logger LOG = LoggerFactory.getLogger(GetTasksByKeyDelegate.class);

    @Override
    public void execute(DelegateExecution execution) throws Exception {

        String taskDefinitionKey = (String) execution.getVariable("task_definition_key");
        Boolean assigneeOnly = (Boolean) execution.getVariable("assignee");
        String startTimeStr = (String) execution.getVariable("start_time");

        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSXXX");
        Date startTime = dateFormat.parse(startTimeStr);

        TaskService taskService = execution.getProcessEngineServices().getTaskService();

        List<Task> tasks;

        if (assigneeOnly != null && assigneeOnly) {
            // Retrieve the assignee from the task itself
            tasks = taskService.createTaskQuery()
                    .taskDefinitionKey(taskDefinitionKey)
                    .taskCreatedAfter(startTime)
                    .active()
                    .initializeFormKeys()
                    .list();

            tasks.removeIf(task -> task.getAssignee() == null || task.getAssignee().isEmpty());
        } else {
            tasks = taskService.createTaskQuery()
                    .taskDefinitionKey(taskDefinitionKey)
                    .taskCreatedAfter(startTime)
                    .active()
                    .initializeFormKeys()
                    .list();
        }

        List<Map<String, Object>> simplifiedTasks = new ArrayList<>();
        for (Task task : tasks) {
            Map<String, Object> simplifiedTask = new HashMap<>();
            simplifiedTask.put("id", task.getId());
            simplifiedTask.put("name", task.getName());
            simplifiedTask.put("assignee", task.getAssignee());
            simplifiedTask.put("owner", task.getOwner());
            simplifiedTask.put("description", task.getDescription());
            simplifiedTask.put("createTime", task.getCreateTime());
            simplifiedTask.put("dueDate", task.getDueDate());
            simplifiedTask.put("priority", task.getPriority());
            simplifiedTask.put("executionId", task.getExecutionId());
            simplifiedTask.put("processInstanceId", task.getProcessInstanceId());
            simplifiedTask.put("processDefinitionId", task.getProcessDefinitionId());
            simplifiedTask.put("taskDefinitionKey", task.getTaskDefinitionKey());
            simplifiedTask.put("parentTaskId", task.getParentTaskId());
            simplifiedTask.put("formKey", task.getFormKey());
            simplifiedTasks.add(simplifiedTask);
        }

        execution.setVariable("tasks", simplifiedTasks);
        LOG.info("Tasks set in execution context: " + simplifiedTasks);

    }
}