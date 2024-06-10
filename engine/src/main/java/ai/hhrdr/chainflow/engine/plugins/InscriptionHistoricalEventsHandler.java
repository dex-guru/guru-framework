package ai.hhrdr.chainflow.engine.plugins;

import ai.hhrdr.chainflow.engine.service.InscriptionSender;
import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.camunda.bpm.engine.impl.history.handler.HistoryEventHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class InscriptionHistoricalEventsHandler implements HistoryEventHandler {

    private static final Logger LOG = LoggerFactory.getLogger(InscriptionHistoricalEventsHandler.class);

    @Autowired
    private InscriptionSender inscriptionSender;

    @Override
    @EventListener
    public void handleEvent(HistoryEvent historyEvent) {
        inscriptionSender.send(historyEvent, historyEvent.getClass().getSimpleName());
    }

    @Override
    public void handleEvents(List<HistoryEvent> historyEvents) {
        for (HistoryEvent historyEvent : historyEvents) {
            handleEvent(historyEvent);
        }
    }
}
