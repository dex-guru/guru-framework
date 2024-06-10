package ai.hhrdr.chainflow.engine.service;

import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.amqp.core.AmqpTemplate;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.core.MessageProperties;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.verify;

public class RabbitMQSenderTest {

    @InjectMocks
    private RabbitMQSender rabbitMQSender;

    @Mock
    private AmqpTemplate rabbitTemplate;

    private MessageConverter messageConverter;

    @BeforeEach
    public void setUp() {
        MockitoAnnotations.openMocks(this);
        messageConverter = new Jackson2JsonMessageConverter();
        rabbitMQSender = new RabbitMQSender(rabbitTemplate, "test-exchange", "test-routingkey", true);
    }

    @Test
    public void testSendAsJsonMessage() {
        // Given
        HistoryEvent event = createHistoryEvent();
        String camundaEventType = "test-type";

        // Capture the arguments
        ArgumentCaptor<String> exchangeCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<String> routingKeyCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<Object> messageCaptor = ArgumentCaptor.forClass(Object.class);

        // When
        rabbitMQSender.send(event, camundaEventType);

        // Then
        verify(rabbitTemplate).convertAndSend(exchangeCaptor.capture(), routingKeyCaptor.capture(), messageCaptor.capture());
        String capturedExchange = exchangeCaptor.getValue();
        String capturedRoutingKey = routingKeyCaptor.getValue();
        Object sentMessage = messageCaptor.getValue();

        assertEquals("test-exchange", capturedExchange);
        assertEquals("test-routingkey", capturedRoutingKey);

        Message message = messageConverter.toMessage(sentMessage, new MessageProperties());
        assertNotNull(message);
        assertEquals("application/json", message.getMessageProperties().getContentType());
    }

    @Test
    public void testSendMessageWithExchangeAndRoutingKey() {
        // Given
        HistoryEvent event = createHistoryEvent();
        String camundaEventType = "test-type";

        // Capture the arguments
        ArgumentCaptor<String> exchangeCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<String> routingKeyCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<Object> messageCaptor = ArgumentCaptor.forClass(Object.class);

        // When
        rabbitMQSender.send(event, camundaEventType);

        // Then
        verify(rabbitTemplate).convertAndSend(exchangeCaptor.capture(), routingKeyCaptor.capture(), messageCaptor.capture());
        String capturedExchange = exchangeCaptor.getValue();
        String capturedRoutingKey = routingKeyCaptor.getValue();
        Object sentMessage = messageCaptor.getValue();

        assertEquals("test-exchange", capturedExchange);
        assertEquals("test-routingkey", capturedRoutingKey);

        Message message = messageConverter.toMessage(sentMessage, new MessageProperties());
        assertNotNull(message);
        assertEquals("application/json", message.getMessageProperties().getContentType());
    }

    private HistoryEvent createHistoryEvent() {
        // Create and return a HistoryEvent object with the necessary properties set.
        // Adjust this method based on the actual available methods of the HistoryEvent class.
        HistoryEvent event = new HistoryEvent();
        // Set necessary properties on the event object here
        // event.setId("12345"); // Example, if setId method exists
        return event;
    }
}
