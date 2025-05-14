import pytest
from unittest.mock import patch, MagicMock
from common import utils
from botocore.exceptions import NoCredentialsError

@patch("common.utils.Web3")
@patch("common.utils.HTTPProvider")
def test_get_web3_client_by_chain_id_all(mock_http, mock_web3):
    # Test default
    w3 = utils.get_web3_client_by_chain_id(None)
    assert mock_web3.called
    # Test known chain IDs
    for chain_id in [261, 8453, 260, 84532]:
        w3 = utils.get_web3_client_by_chain_id(chain_id)
        assert mock_web3.called
    # Test unsupported chain ID
    with pytest.raises(ValueError):
        utils.get_web3_client_by_chain_id(9999)

@patch("common.utils.ExternalTaskWorker")
def test_setup_worker(mock_worker):
    def handler(task):
        return "ok"
    utils.setup_worker("topic", handler)
    assert mock_worker.called
    # Test with multiple topics
    utils.setup_worker(["topic1", "topic2"], handler)
    assert mock_worker.called

@patch("common.utils.boto3.client")
@patch("common.utils.settings")
def test_upload_file_to_s3_binary_success(mock_settings, mock_boto3):
    mock_settings.AWS_ACCESS_KEY_ID = "key"
    mock_settings.AWS_SECRET_ACCESS_KEY = "secret"
    mock_settings.AWS_REGION_NAME = "region"
    mock_settings.AWS_S3_BUCKET_NAME = "bucket"
    mock_s3 = MagicMock()
    mock_boto3.return_value = mock_s3
    url = utils.upload_file_to_s3_binary(b"data", "file.txt")
    assert url.startswith("https://img.burning.meme/")
    mock_s3.put_object.assert_called_once()

@patch("common.utils.boto3.client")
@patch("common.utils.settings")
def test_upload_file_to_s3_binary_no_credentials(mock_settings, mock_boto3):
    mock_settings.AWS_ACCESS_KEY_ID = "key"
    mock_settings.AWS_SECRET_ACCESS_KEY = "secret"
    mock_settings.AWS_REGION_NAME = "region"
    mock_settings.AWS_S3_BUCKET_NAME = "bucket"
    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = NoCredentialsError()
    mock_boto3.return_value = mock_s3
    url = utils.upload_file_to_s3_binary(b"data", "file.txt")
    assert url is None

@patch("common.utils.Web3")
@patch("common.utils.HTTPProvider")
def test_get_web3_client_by_chain_id_unsupported(mock_http, mock_web3):
    with pytest.raises(ValueError) as excinfo:
        utils.get_web3_client_by_chain_id(9999)
    assert "Unsupported chain ID" in str(excinfo.value)

@patch("common.utils.boto3.client")
@patch("common.utils.settings")
def test_upload_file_to_s3_binary_generic_error(mock_settings, mock_boto3):
    mock_settings.AWS_ACCESS_KEY_ID = "key"
    mock_settings.AWS_SECRET_ACCESS_KEY = "secret"
    mock_settings.AWS_REGION_NAME = "region"
    mock_settings.AWS_S3_BUCKET_NAME = "bucket"
    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = Exception("S3 error")
    mock_boto3.return_value = mock_s3
    with pytest.raises(Exception) as excinfo:
        utils.upload_file_to_s3_binary(b"data", "file.txt")
    assert "S3 error" in str(excinfo.value) 