package ai.hhrdr.chainflow.engine.plugins;

import ai.hhrdr.chainflow.engine.service.InscriptionSender;
import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.camunda.bpm.engine.impl.history.event.HistoryEventTypes;
import org.camunda.bpm.engine.impl.history.handler.HistoryEventHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Component
public class InscriptionHistoricalEventsHandler implements HistoryEventHandler {

    private static final Logger LOG = LoggerFactory.getLogger(InscriptionHistoricalEventsHandler.class);

    @Autowired
    private InscriptionSender inscriptionSender;

    @Value("${inscription.enabled:false}")
    private boolean inscriptionsHistoryEnabled;

    @Value("${inscription.event.types:ALL}")
    private String eventTypesConfig;

    private Set<String> eventTypeSet;

    @PostConstruct
    public void init() {
        if ("ALL".equalsIgnoreCase(eventTypesConfig)) {
            eventTypeSet = getDefaultEventTypes();
        } else {
            eventTypeSet = new HashSet<>(Arrays.asList(eventTypesConfig.split(",")));
        }
    }

    @Override
    @EventListener
    public void handleEvent(HistoryEvent historyEvent) {
        if (inscriptionsHistoryEnabled && shouldHandleEvent(historyEvent)) {
            inscriptionSender.send(historyEvent, historyEvent.getEventType());
        } else {
            LOG.info("Inscriptions are disabled or event type not configured to handle. Event not handled: " + historyEvent.getEventType());
        }
    }

    @Override
    public void handleEvents(List<HistoryEvent> historyEvents) {
        if (inscriptionsHistoryEnabled) {
            for (HistoryEvent historyEvent : historyEvents) {
                if (shouldHandleEvent(historyEvent)) {
                    handleEvent(historyEvent);
                }
            }
        } else {
            LOG.info("Inscriptions are disabled. Events not handled.");
        }
    }

    private boolean shouldHandleEvent(HistoryEvent historyEvent) {
        return eventTypeSet.contains(historyEvent.getEventType());
    }

    private Set<String> getDefaultEventTypes() {
        return new HashSet<>(Arrays.asList(
                HistoryEventTypes.ACTIVITY_INSTANCE_START.getEventName(),
                HistoryEventTypes.ACTIVITY_INSTANCE_END.getEventName(),
                HistoryEventTypes.TASK_INSTANCE_CREATE.getEventName(),
                HistoryEventTypes.TASK_INSTANCE_UPDATE.getEventName(),
                HistoryEventTypes.TASK_INSTANCE_COMPLETE.getEventName(),
                HistoryEventTypes.TASK_INSTANCE_DELETE.getEventName(),
                HistoryEventTypes.VARIABLE_INSTANCE_CREATE.getEventName(),
                HistoryEventTypes.VARIABLE_INSTANCE_UPDATE.getEventName(),
                HistoryEventTypes.VARIABLE_INSTANCE_DELETE.getEventName(),
                HistoryEventTypes.FORM_PROPERTY_UPDATE.getEventName(),
                HistoryEventTypes.INCIDENT_CREATE.getEventName(),
                HistoryEventTypes.INCIDENT_DELETE.getEventName(),
                HistoryEventTypes.INCIDENT_RESOLVE.getEventName(),
                HistoryEventTypes.IDENTITY_LINK_ADD.getEventName(),
                HistoryEventTypes.IDENTITY_LINK_DELETE.getEventName()
        ));
    }
}