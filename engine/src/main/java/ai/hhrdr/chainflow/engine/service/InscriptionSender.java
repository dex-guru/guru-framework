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
import java.util.List;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Service
public class InscriptionSender implements DisposableBean {

    private final BlockingQueue<HistoryEvent> eventQueue;
    private final int batchSize;
    private final long blockTime;

    @Autowired
    private InscriptionDataService inscriptionDataService;

    private final Logger LOG = LoggerFactory.getLogger(InscriptionSender.class);
    private Thread workerThread;

    public InscriptionSender(
            @Value("${inscription.queue.capacity}") Integer queueCapacity,
            @Value("${inscription.batch.size}") Integer batchSize,
            @Value("${inscription.block.time}") Long blockTime
    ) {
        // Initialize the queue with the specified capacity
        this.eventQueue = new LinkedBlockingQueue<>(queueCapacity);
        this.batchSize = batchSize;
        this.blockTime = blockTime;
    }

    @PostConstruct
    public void init() {
        workerThread = new Thread(this::processEvents);
        workerThread.start();
    }

    public void send(HistoryEvent event, String camundaEventType) {
        if (!eventQueue.offer(event)) {
            // If the queue is full, remove the oldest event to make space for the new one
            eventQueue.poll();
            eventQueue.offer(event);
            LOG.warn("Event queue overflow. Oldest event removed to make space for new event: " + event);
        }
    }

    private void processEvents() {
        while (true) {
            try {
                List<HistoryEvent> events = pollBatchEvents();
                if (!events.isEmpty()) {
                    List<String> jsonDataList = events.stream()
                            .map(event -> {
                                try {
                                    return new ObjectMapper().writeValueAsString(event);
                                } catch (Exception e) {
                                    LOG.error("Error serializing event: " + e.getMessage(), e);
                                    return null;
                                }
                            })
                            .filter(data -> data != null)
                            .collect(Collectors.toList());

                    inscriptionDataService.sendInscriptionData(jsonDataList);
                    LOG.debug("Sent asynchronously, batch size = " + jsonDataList.size());
                }
                Thread.sleep(blockTime); // sleep for the block time between batches
            } catch (Exception e) {
                LOG.error("Error sending inscriptions data asynchronously", e);
            }
        }
    }

    private List<HistoryEvent> pollBatchEvents() throws InterruptedException {
        List<HistoryEvent> events = new java.util.ArrayList<>();
        for (int i = 0; i < batchSize; i++) {
            HistoryEvent event = eventQueue.poll(1, TimeUnit.SECONDS);
            if (event != null) {
                events.add(event);
            } else {
                break;
            }
        }
        return events;
    }

    @Override
    public void destroy() throws Exception {
        if (workerThread != null && workerThread.isAlive()) {
            workerThread.interrupt();
        }
    }
}
