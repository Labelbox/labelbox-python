import random
import argparse
import time
import random
import csv
import os
import time
import datetime
from google.cloud import storage


def main(output_dir, output_name):

    print(os.environ)

    # Make some random data
    WORDS = ('dog', 'cat', 'giraffe', 'avocado', 'sloth', 'penguin', 'foo', 'bar', 'baz')
    with open(output_name, 'w') as f_out:
        wr = csv.writer(f_out)
        for l in range(0, 100):
            line = [l]
            for col in range(0, 5):
                line.append(random.choice(WORDS))
            wr.writerow(line)
            print(l)
            #time.sleep(1)

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
