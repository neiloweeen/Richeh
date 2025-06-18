import os
import b2sdk.v2 as b2
from dotenv import load_dotenv

load_dotenv()

info = b2.InMemoryAccountInfo()
b2_api = b2.B2Api(info)

application_key_id = os.getenv("B2_KEY_ID")
application_key = os.getenv("B2_APPLICATION_KEY")

b2_api.authorize_account("production", application_key_id, application_key)

bucket = b2_api.get_bucket_by_name("cubari-image-dump")

def upload_to_bucket(file_name, bytes_data):
    f_data = bucket.upload_bytes(bytes_data, file_name)
    return b2_api.get_download_url_for_fileid(f_data.id_)
# bucket.upload_bytes(b"Hello, World!", "hello.txt")