import random
import argparse
import time
import random
import csv
import os
import time
import datetime
from google.cloud import storage
from google.cloud import secretmanager
from labelbox import Client

def main(output_dir, output_name):

    secret_client = secretmanager.SecretManagerServiceClient()
    secret_name = f'projects/564464872598/secrets/jbuhler-apikey/versions/1'

    secret = secret_client.access_secret_version(request={"name": secret_name})
    API_KEY = secret.payload.data.decode("utf-8")
    ENDPOINT = "https://api.labelbox.com/graphql"

    lb = Client(api_key=API_KEY, endpoint=ENDPOINT)

    with open(output_name, 'w') as f_out:
        wr = csv.writer(f_out)
        for p in lb.get_projects():
            line = [p.name, p.uid, p.description]
            wr.writerow(line)

    bucket = storage.Client().bucket(output_dir)
    blob = bucket.blob('{}/{}'.format(
        datetime.datetime.now().strftime('custom_%Y%m%d_%H%M%S'),
        output_name))
    blob.upload_from_filename(output_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vertex AI Custom Container Test')
    parser.add_argument('--output-dir',
                        type=str,
                        help='Where to save the output')
    parser.add_argument('--output-name',
                        type=str,
                        default='custom-test',
                        help='What to name the saved file')
    args = parser.parse_args()
    main(**vars(args))
