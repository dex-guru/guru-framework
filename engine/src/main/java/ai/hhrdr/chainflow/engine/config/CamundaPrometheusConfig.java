package ai.hhrdr.chainflow.engine.config;

import io.digitalstate.camunda.prometheus.PrometheusProcessEnginePlugin;
import org.camunda.bpm.engine.ProcessEngineConfiguration;
import org.camunda.bpm.engine.impl.cfg.ProcessEngineConfigurationImpl;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;

import java.io.IOException;
import java.util.List;

@Configuration
public class CamundaPrometheusConfig {

    @Bean
    public PrometheusProcessEnginePlugin prometheusProcessEnginePlugin() throws IOException {
        PrometheusProcessEnginePlugin plugin = new PrometheusProcessEnginePlugin();
        plugin.setPort("9999"); // Make sure this matches the port you set in your application.yaml
        plugin.setCamundaReportingIntervalInSeconds("5");

        Resource resource = new ClassPathResource("prometheus-metrics.yml");
        plugin.setCollectorYmlFilePath(resource.getFile().getAbsolutePath()); // Resolve classpath resource to absolute path

        return plugin;
    }

    @Bean
    public ProcessEngineConfiguration processEngineConfiguration(PrometheusProcessEnginePlugin prometheusPlugin) {
        ProcessEngineConfigurationImpl configuration = (ProcessEngineConfigurationImpl) ProcessEngineConfiguration.createStandaloneInMemProcessEngineConfiguration();
        configuration.setProcessEnginePlugins(List.of(prometheusPlugin));
        return configuration;
    }
}
