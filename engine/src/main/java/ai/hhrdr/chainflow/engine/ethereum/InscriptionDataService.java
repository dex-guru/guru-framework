package ai.hhrdr.chainflow.engine.ethereum;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.web3j.crypto.Credentials;
import org.web3j.protocol.Web3j;
import org.web3j.protocol.core.methods.response.EthSendTransaction;
import org.web3j.protocol.http.HttpService;
import org.web3j.tx.RawTransactionManager;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;

@Service
public class InscriptionDataService {

    private final Web3j web3j;
    private final Credentials credentials;
    private final BigInteger gasLimit = BigInteger.valueOf(60000);
    private final Integer chainId;
    private final Integer maxRetry;

    private static final Logger LOG = LoggerFactory.getLogger(InscriptionDataService.class);

    public InscriptionDataService(@Value("${inscription.privateKey}") String privateKey,
                                  @Value("${inscription.rpcUrl}") String rpcUrl,
                                  @Value("${inscription.chainId}") Integer chainId,
                                  @Value("${inscription.maxRetry}") Integer maxRetry) {
        this.web3j = Web3j.build(new HttpService(rpcUrl));
        this.credentials = Credentials.create(privateKey);
        this.chainId = chainId;
        this.maxRetry = maxRetry;
    }

    public void sendInscriptionData(String jsonData) {
        try {
            String prefixedData = "data:application/json," + jsonData;
            String hexData = "0x" + bytesToHex(prefixedData.getBytes(StandardCharsets.UTF_8));
            sendRawTransactionWithRetries(hexData);
        } catch (Exception e) {
            LOG.error("Error while sending inscription data: " + e.getMessage(), e);
        }
    }

    private void sendRawTransactionWithRetries(String hexData) throws Exception {
        BigInteger gasPrice = web3j.ethGasPrice().send().getGasPrice();
        gasPrice = gasPrice.add(gasPrice.divide(BigInteger.valueOf(5)));

        RawTransactionManager transactionManager = new RawTransactionManager(web3j, credentials, chainId);

        boolean success = false;
        int attempts = 0;

        while (!success && attempts < maxRetry) {
            try {
                // Send transaction to self address
                String transactionAddress = credentials.getAddress();
                EthSendTransaction ethSendTransaction = transactionManager.sendTransaction(gasPrice, gasLimit, transactionAddress, hexData, BigInteger.ZERO);

                if (ethSendTransaction.hasError()) {
                    LOG.error("Transaction Error: " + ethSendTransaction.getError().getMessage());
                    TimeUnit.SECONDS.sleep((long) Math.pow(2, attempts));  // Exponential backoff
                } else {
                    LOG.info("Transaction Hash: " + ethSendTransaction.getTransactionHash());
                    success = true;
                }
            } catch (Exception e) {
                LOG.error("Error sending transaction: " + e.getMessage(), e);
                TimeUnit.SECONDS.sleep((long) Math.pow(2, attempts));  // Exponential backoff
            }
            attempts++;
        }

        if (!success) {
            LOG.error("Failed to send transaction after {} attempts", maxRetry);
        }
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
