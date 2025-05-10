package ai.hhrdr.chainflow.engine;

import org.camunda.bpm.spring.boot.starter.annotation.EnableProcessApplication;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.scheduling.annotation.EnableScheduling;

import org.camunda.connect.plugin.impl.ConnectProcessEnginePlugin;

import org.camunda.bpm.engine.rest.security.auth.ProcessEngineAuthenticationFilter;
import org.camunda.bpm.spring.boot.starter.annotation.EnableProcessApplication;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.transaction.PlatformTransactionManager;

import javax.servlet.Filter;
import javax.sql.DataSource;

@SpringBootApplication
@EnableScheduling
@Configuration
@EnableProcessApplication("chainflow-engine")
public class CamundaApplication extends SpringBootServletInitializer {

  public static void main(String... args) {
    SpringApplication.run(CamundaApplication.class, args);
  }


  /**
   * Spring Servlet Initializer
   *
   * @param application application
   * @return SpringApplicationBuilder
   */
  @Override
  protected SpringApplicationBuilder configure(SpringApplicationBuilder application) {
    return application.sources(CamundaApplication.class);
  }

  /**
   * Property placeholder configurer needed to process @Value annotations
   */
  @Bean
  public static PropertySourcesPlaceholderConfigurer propertyConfigurer() {
    return new PropertySourcesPlaceholderConfigurer();
  }

  @Bean
  public ConnectProcessEnginePlugin connectProcessEnginePlugin() {
    return new ConnectProcessEnginePlugin();
  }


  @Bean
  public PlatformTransactionManager transactionManager() {
    return new DataSourceTransactionManager(camundaDataSource());
  }
  @Bean(name="camundaBpmDataSource")
  @Primary
  @ConfigurationProperties(prefix="camunda.bpm.datasource")
  public DataSource camundaDataSource() {
    return DataSourceBuilder.create().build();
  }

  @Bean
  public FilterRegistrationBean authenticationFilter() {
    FilterRegistrationBean registration = new FilterRegistrationBean();
    Filter myFilter = new ProcessEngineAuthenticationFilter();
    registration.setFilter(myFilter);
    registration.addUrlPatterns("/engine-rest/*");
    registration.addInitParameter("authentication-provider",
            "ai.hhrdr.chainflow.engine.config.JwtAuthenticationFilter");
    registration.setName("camunda-auth");
    registration.setOrder(1);
    return registration;
  }

}
