package ai.hhrdr.chainflow.engine.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class FilterConfig {
    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter(JwtConfig jwtConfig) {
        return new JwtAuthenticationFilter(jwtConfig);
    }
} 