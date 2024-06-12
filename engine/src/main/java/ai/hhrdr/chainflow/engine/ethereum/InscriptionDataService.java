package ai.hhrdr.chainflow.engine.ethereum;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.web3j.crypto.Credentials;
import org.web3j.crypto.RawTransaction;
import org.web3j.crypto.TransactionEncoder;
import org.web3j.protocol.Web3j;
import org.web3j.protocol.core.BatchRequest;
import org.web3j.protocol.core.BatchResponse;
import org.web3j.protocol.core.DefaultBlockParameterName;
import org.web3j.protocol.core.methods.request.Transaction;
import org.web3j.protocol.core.methods.response.EthSendTransaction;
import org.web3j.protocol.core.methods.response.EthSendTransaction;
import org.web3j.protocol.http.HttpService;
import org.web3j.tx.RawTransactionManager;
import org.web3j.utils.Numeric;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;

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

    public void sendInscriptionData(List<String> jsonDataList) {
        try {
            BatchRequest batchRequest = web3j.newBatch();
            BigInteger gasPrice = web3j.ethGasPrice().send().getGasPrice();
            gasPrice = gasPrice.add(gasPrice.divide(BigInteger.valueOf(5)));

            String transactionAddress = credentials.getAddress();
            BigInteger nonce = web3j.ethGetTransactionCount(transactionAddress, DefaultBlockParameterName.PENDING).send().getTransactionCount();

            for (String jsonData : jsonDataList) {
                String prefixedData = "data:application/json," + jsonData;
                String hexData = "0x" + bytesToHex(prefixedData.getBytes(StandardCharsets.UTF_8));

                RawTransaction rawTransaction = RawTransaction.createTransaction(
                        nonce,
                        gasPrice,
                        gasLimit,
                        transactionAddress,
                        BigInteger.ZERO,
                        hexData);

                byte[] signedMessage = TransactionEncoder.signMessage(rawTransaction, chainId, credentials);
                String hexValue = Numeric.toHexString(signedMessage);

                batchRequest.add(web3j.ethSendRawTransaction(hexValue));
                nonce = nonce.add(BigInteger.ONE); // Increment nonce for the next transaction
            }

            BatchResponse batchResponse = batchRequest.send();
            handleBatchResponse(batchResponse);
        } catch (Exception e) {
            LOG.error("Error while sending inscription data: " + e.getMessage(), e);
        }
    }

    private void handleBatchResponse(BatchResponse batchResponse) {
        batchResponse.getResponses().forEach(response -> {
            EthSendTransaction ethSendTransaction = (EthSendTransaction) response;
            if (ethSendTransaction.hasError()) {
                LOG.error("Transaction Error: " + ethSendTransaction.getError().getMessage());
            } else {
                LOG.info("Transaction Hash: " + ethSendTransaction.getTransactionHash());
            }
        });
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
