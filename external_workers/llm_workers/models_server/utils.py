import os

import boto3
from botocore.exceptions import NoCredentialsError

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION_NAME = os.getenv('AWS_REGION', 'us-east-2')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')


def upload_file_to_s3_binary(content: bytes, s3_file_name) -> str:
    """
    Uploads binary content to AWS S3 and returns the file URL.

    Parameters:
    - content: Binary content of the file to upload.
    - bucket_name: Name of the S3 bucket.
    - s3_file_name: Object name in S3.

    Returns:
    - URL of the uploaded file on success.
    """
    s3 = boto3.client('s3',
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION_NAME)
    try:
        s3.put_object(Bucket=AWS_S3_BUCKET_NAME, Key=s3_file_name, Body=content)
        location = s3.get_bucket_location(Bucket=AWS_S3_BUCKET_NAME)['LocationConstraint']
        url = f"https://{AWS_S3_BUCKET_NAME}.s3.{location}.amazonaws.com/{s3_file_name}"
        return url
    except NoCredentialsError:
        print("Credentials not available")
        return None
