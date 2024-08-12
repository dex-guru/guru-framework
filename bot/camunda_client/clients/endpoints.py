from typing import ClassVar


class ExternalTaskUrls:
    _base_path: ClassVar[str] = "/external-task"

    fetch_and_lock = f"{_base_path}/fetchAndLock"

    @classmethod
    def complete(cls, ident: str) -> str:
        return f"{cls._base_path}/{ident}/complete"

    @classmethod
    def failure(cls, ident: str) -> str:
        return f"{cls._base_path}/{ident}/failure"

    @classmethod
    def extend_lock(cls, ident: str) -> str:
        return f"{cls._base_path}/{ident}/extendLock"

    @classmethod
    def unlock(cls, ident: str) -> str:
        return f"{cls._base_path}/{ident}/unlock"

    @classmethod
    def bpmn_error(cls, ident: str) -> str:
        return f"{cls._base_path}/{ident}/bpmnError"


class CamundaUrls:
    external_task = ExternalTaskUrls()

    deployment_create = "/deployment/create"
    message_send = "/message"
    user_create = "/user/create"
    user = "/user"
    group = "/group"
    process_instances = "/process-instance"
    process_definitions = "/process-definition"
    task = "/task"
    tasks_count = f"{task}/count"
    history_task = "/history/task"
    variable_instances = "/history/variable-instance"

    @staticmethod
    def get_start_process_instance(
        process_key: str,
        tenant_id: str | None = None,
    ) -> str:
        if tenant_id:
            return f"/process-definition/key/{process_key}/tenant-id/{tenant_id}/start"
        return f"/process-definition/key/{process_key}/start"

    @staticmethod
    def get_process_instance(process_instance_id: str) -> str:
        return f"/process-instance/{process_instance_id}"

    @classmethod
    def get_profile_by_user_id(cls, ident: str) -> str:
        return f"{cls.user}/{ident}/profile"

    @classmethod
    def get_task_by_id(cls, ident: str) -> str:
        return f"{cls.task}/{ident}"

    @classmethod
    def submit_task_form(cls, task_id: str) -> str:
        return f"{cls.task}/{task_id}/submit-form"

    @classmethod
    def complete_task(cls, task_id: str) -> str:
        return f"{cls.task}/{task_id}/complete"

    @classmethod
    def get_task_form_variables(cls, task_id: str) -> str:
        return f"{cls.task}/{task_id}/form-variables"

    @classmethod
    def get_task_variables(cls, task_id: str) -> str:
        return f"{cls.task}/{task_id}/variables"

    @classmethod
    def claim_task(cls, task_id: str) -> str:
        return f"{cls.task}/{task_id}/claim"

    @classmethod
    def unclaim_task(cls, task_id: str) -> str:
        return f"{cls.task}/{task_id}/unclaim"

    @classmethod
    def set_assignee_task(cls, task_id: str) -> str:
        return f"{cls.task}/{task_id}/assignee"

    @classmethod
    def group_create_member(cls, group_id: str, user_id: str) -> str:
        return f"{cls.group}/{group_id}/members/{user_id}"

    @classmethod
    def get_process_instance_suspend(cls, process_instance_id: str) -> str:
        return f"{cls.process_instances}/{process_instance_id}/suspended"

    @classmethod
    def get_url_process_instances_count(cls) -> str:
        return f"{cls.process_instances}/count"

    @classmethod
    def get_process_instance_variable(cls, process_instance_id: str) -> str:
        return f"{cls.process_instances}/{process_instance_id}/variables"
