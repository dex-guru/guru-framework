package ai.hhrdr.chainflow.engine;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import java.util.Objects;
import org.camunda.bpm.engine.ManagementService;
import org.camunda.bpm.engine.ProcessEngine;
import org.camunda.bpm.engine.management.Metrics;
import org.camunda.bpm.engine.management.MetricsQuery;
import org.camunda.bpm.engine.query.Query;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class CamundaMonitoringMetrics {

    private static final String NUMBER_OF_EXCLUSIVE_JOBS = "Number of exclusive jobs";
    private static final String NUMBER_OF_ACQUISITION_CYCLES = "Number of acquisition cycles";
    private static final String NUMBER_OF_JOBS = "Number of jobs";
    private static final String NUMBER_OF_DECISIONS = "Number of decisions";
    private static final String NUMBER_OF_FLOW_NODES = "Number of flow nodes";
    private static final String NUMBER_OF_TASK_USERS = "Number of task users";
    private static final String NUMBER_OF_UNIQUE_TASK_WORKERS = "Number of unique task workers";

    private final ManagementService service;

    public CamundaMonitoringMetrics(ProcessEngine engine) {
        super();
        Objects.requireNonNull(engine);
        this.service = engine.getManagementService();
    }

    @Bean
    public Gauge jobExecutionsSuccessful(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.JOB_SUCCESSFUL);

        return Gauge.builder("job.executions.successful", query::sum)
                .description("Successful job executions")
                .baseUnit(NUMBER_OF_JOBS)
                .register(registry);
    }

    @Bean
    public Gauge jobExecutionsFailed(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.JOB_FAILED);

        return Gauge.builder("job.executions.failed", query::sum)
                .description("Failed job executions")
                .baseUnit(NUMBER_OF_JOBS)
                .register(registry);
    }

    @Bean
    public Gauge jobExecutionsRejected(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.JOB_EXECUTION_REJECTED);

        return Gauge.builder("job.executions.rejected", query::sum)
                .description("Rejected jobs due to saturated execution resources")
                .baseUnit(NUMBER_OF_JOBS)
                .register(registry);
    }

    @Bean
    public Gauge jobAcquisitionsAttempted(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.JOB_ACQUISITION_ATTEMPT);

        return Gauge.builder("job.acquisitions.attempted", query::sum)
                .description("Performed job acquisition cycles")
                .baseUnit(NUMBER_OF_ACQUISITION_CYCLES)
                .register(registry);
    }

    @Bean
    public Gauge jobAcquisitionsSuccessful(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.JOB_ACQUIRED_SUCCESS);

        return Gauge.builder("job.acquisitions.successful", query::sum)
                .description("Successful job acquisitions")
                .baseUnit(NUMBER_OF_JOBS)
                .register(registry);
    }

    @Bean
    public Gauge jobAcquistionsFailed(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.JOB_ACQUIRED_FAILURE);

        return Gauge.builder("job.acquisitions.failed", query::sum)
                .description("Failed job acquisitions")
                .baseUnit(NUMBER_OF_JOBS)
                .register(registry);
    }

    @Bean
    public Gauge jobLocksExclusive(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.JOB_LOCKED_EXCLUSIVE);

        return Gauge.builder("job.locks.exclusive", query::sum)
                .description("Exclusive jobs that are immediately locked and executed")
                .baseUnit(NUMBER_OF_EXCLUSIVE_JOBS)
                .register(registry);
    }

    @Bean
    public Gauge dueJobsInDB(MeterRegistry registry) {
        Query jobQuery = service.createJobQuery().executable().messages();

        return Gauge.builder("jobs.due", jobQuery::count)
                .description("Jobs from async continuation that are due").register(registry);
    }


    @Bean
    public Gauge decisionInstances(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.DECISION_INSTANCES);

        return Gauge.builder("decision.instances", query::sum)
                .description("Number of decision instances")
                .baseUnit(NUMBER_OF_DECISIONS)
                .register(registry);
    }

    @Bean
    public Gauge executedDecisionElements(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.EXECUTED_DECISION_ELEMENTS);

        return Gauge.builder("executed.decision.elements", query::sum)
                .description("Number of executed decision elements")
                .baseUnit(NUMBER_OF_DECISIONS)
                .register(registry);
    }

    @Bean
    public Gauge executedDecisionInstances(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.EXECUTED_DECISION_INSTANCES);

        return Gauge.builder("executed.decision.instances", query::sum)
                .description("Number of executed decision instances")
                .baseUnit(NUMBER_OF_DECISIONS)
                .register(registry);
    }

    @Bean
    public Gauge flowNodeInstances(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.FLOW_NODE_INSTANCES);

        return Gauge.builder("flow.node.instances", query::sum)
                .description("Number of flow node instances")
                .baseUnit(NUMBER_OF_FLOW_NODES)
                .register(registry);
    }

    @Bean
    public Gauge processInstances(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.PROCESS_INSTANCES);

        return Gauge.builder("process.instances", query::sum)
                .description("Number of process instances")
                .register(registry);
    }

    @Bean
    public Gauge rootProcessInstanceStart(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.ROOT_PROCESS_INSTANCE_START);

        return Gauge.builder("root.process.instance.start", query::sum)
                .description("Number of root process instance starts")
                .register(registry);
    }

    @Bean
    public Gauge taskUsers(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.TASK_USERS);

        return Gauge.builder("task.users", query::sum)
                .description("Number of task users")
                .baseUnit(NUMBER_OF_TASK_USERS)
                .register(registry);
    }

    @Bean
    public Gauge uniqueTaskWorkers(MeterRegistry registry) {
        MetricsQuery query = service.createMetricsQuery().name(Metrics.UNIQUE_TASK_WORKERS);

        return Gauge.builder("unique.task.workers", query::sum)
                .description("Number of unique task workers")
                .baseUnit(NUMBER_OF_UNIQUE_TASK_WORKERS)
                .register(registry);
    }
}
