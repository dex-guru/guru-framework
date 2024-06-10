package ai.hhrdr.chainflow.engine.service;

import ai.hhrdr.chainflow.engine.ethereum.InscriptionDataService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

@Service
public class InscriptionSender implements DisposableBean {

    @Autowired
    private InscriptionDataService inscriptionDataService;

    @Value("${inscription.enabled}")
    private Boolean enabled;

    private final BlockingQueue<HistoryEvent> eventQueue = new LinkedBlockingQueue<>();
    private final Thread workerThread;

    private static final Logger LOG = LoggerFactory.getLogger(InscriptionSender.class);

    public InscriptionSender() {
        workerThread = new Thread(this::processEvents);
        workerThread.start();
    }

    public void send(HistoryEvent event, String camundaEventType) {
        if (enabled) {
            eventQueue.add(event);
        } else {
            LOG.info("Event skipped, inscriptions disabled, eventType = " + camundaEventType + ", msg = " + event);
        }
    }

    private void processEvents() {
        while (true) {
            try {
                HistoryEvent event = eventQueue.take();
                String jsonData = new ObjectMapper().writeValueAsString(event);
                inscriptionDataService.sendInscriptionData(jsonData);
                LOG.debug("Sent asynchronously, eventType = " + event.getClass().getSimpleName() + ", msg = " + jsonData);
            } catch (Exception e) {
                LOG.error("Error sending inscriptions data asynchronously", e);
            }
        }
    }

    @Override
    public void destroy() throws Exception {
        workerThread.interrupt();
    }
}
