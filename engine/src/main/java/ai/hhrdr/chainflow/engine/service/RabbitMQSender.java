package ai.hhrdr.chainflow.engine.service;

import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.amqp.core.AmqpTemplate;

@Service
public class RabbitMQSender {

    private final AmqpTemplate rabbitTemplate;
    private final String exchange;
    private final String routingkey;
    private final Boolean enabled;

    private static final Logger LOG = LoggerFactory.getLogger(RabbitMQSender.class);

    public RabbitMQSender(AmqpTemplate rabbitTemplate,
                          @Value("${engine.rabbitmq.exchange}") String exchange,
                          @Value("${engine.rabbitmq.routingkey}") String routingkey,
                          @Value("${spring.rabbitmq.enabled}") Boolean enabled) {
        this.rabbitTemplate = rabbitTemplate;
        this.exchange = exchange;
        this.routingkey = routingkey;
        this.enabled = enabled;
    }

    public void send(HistoryEvent event, String camundaEventType) {
        if (enabled) {
            rabbitTemplate.convertAndSend(exchange, routingkey, event);
            LOG.debug("Send, eventType = " + camundaEventType + " msg = " + event);
        } else {
            LOG.info("Event skipped, rabbit disabled, eventType = " + camundaEventType + " msg = " + event);
        }
    }
}
