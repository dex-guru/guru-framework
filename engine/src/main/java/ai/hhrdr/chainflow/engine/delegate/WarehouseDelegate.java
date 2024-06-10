package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.camunda.bpm.engine.impl.persistence.entity.ExecutionEntity;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.logging.Logger;

@Component("warehouse")
public class WarehouseDelegate implements JavaDelegate {

  @Value("${api.url}")
  private String apiURL;

  @Value("${api.key}")
  private String apiKey;

  private static final Logger LOGGER = Logger.getLogger(WarehouseDelegate.class.getName());

  public void execute(DelegateExecution execution) throws Exception {

    LOGGER.info("\n\n  ... WarehouseDelegate invoked by "
            + "activityName='" + execution.getCurrentActivityName() + "'"
            + ", activityId=" + execution.getCurrentActivityId()
            + ", processDefinitionId=" + execution.getProcessDefinitionId()
            + ", processInstanceId=" + execution.getProcessInstanceId()
            + ", businessKey=" + execution.getProcessBusinessKey()
            + ", executionId=" + execution.getId()
            + ", variables=" + execution.getVariables()
            + " \n\n");

    String json = "{\"is_draft\":false}";
    HttpClient client = HttpClient.newHttpClient();
    switch (((ExecutionEntity) execution).getProcessDefinition().getKey()) {
      case "warehouse_dashboard_review":
        try {
          HttpRequest req = HttpRequest
                  .newBuilder()
                  .uri(URI.create(apiURL + "/api/dashboards/" + execution.getVariable("dashboard_id")))
                  .header("Content-Type", "application/json")
                  .header("Authorization", apiKey)
                  .POST(HttpRequest.BodyPublishers.ofString(json))
                  .build();
          sendRequest(client, req);
        }
        catch (Exception e) {
          LOGGER.severe("Warehouse Delegate failed to update Dashboard. \nException: " + e.getMessage());
        }
        break;
      case "warehouse_query_review":
        try {
          HttpRequest req = HttpRequest
                  .newBuilder()
                  .uri(URI.create(apiURL + "/api/queries/" + execution.getVariable("query_id")))
                  .header("Content-Type", "application/json")
                  .header("Authorization", apiKey)
                  .POST(HttpRequest.BodyPublishers.ofString(json))
                  .build();
          sendRequest(client, req);
        }
        catch (Exception e) {
          LOGGER.severe("Warehouse Delegate failed to update Query. \nException: " + e.getMessage());
        }
        break;
    }
  }

  private static void sendRequest(HttpClient client, HttpRequest req) {
    try {
      HttpResponse<String> response = client.send(req, HttpResponse.BodyHandlers.ofString());
      LOGGER.info("Publish Response Code: " + response.statusCode() + "\nPublish Response Body: " + response.body());
    } catch (IOException | InterruptedException e) {
      LOGGER.severe("Error while sending HTTP request: " + e.getMessage());
    }
  }
}

