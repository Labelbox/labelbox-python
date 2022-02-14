import os
import argparse
import sys
import operator
from google.cloud import aiplatform
from prettytable import PrettyTable


def list_objects(object_types, attrs):

    # Use 'id' instead of 'name' since Google uses 'id' in the interface
    # but 'name' in the attributes
    display_attrs = ['id' if x == 'name' else x for x in attrs]
    for t in object_types:
        objs = getattr(aiplatform, t).list()
        if objs:
            table = PrettyTable(display_attrs,
                                horizontal_char='—',
                                vertical_char='│',
                                junction_char=' ')
            table.title = t
            table.align = "l"
            for obj in objs:
                row = []
                for attr in attrs:
                    # using attrgetter in order to get state.name for jobs
                    row.append(operator.attrgetter(attr)(obj))
                table.add_row(row)
            print(table)


def delete_object(object_types, object_id):
    for t in object_types:
        objs = getattr(aiplatform, t).list()
        for obj in objs:
            if obj.name == object_id:
                print("DELETING " + obj.display_name)

                # undeploy models from endpoints
                if hasattr(obj, 'undeploy_all'):
                    obj.undeploy_all()
                obj.delete()


def main():
    parser = argparse.ArgumentParser(description='List and Delete Vertex '
                                     'AI objects')
    parser.add_argument("--datasets", action="store_true", help='List datasets')
    parser.add_argument("--models", action="store_true", help='List models')
    parser.add_argument("--jobs", action="store_true", help='List jobs')
    parser.add_argument("--endpoints",
                        action="store_true",
                        help='List endpoints')
    parser.add_argument("--all", action="store_true", help='List all objects')
    parser.add_argument("--delete", help='id of the object to delete. ')

    # Print argparse help by default
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    print('You can also manage datasets, models, jobs and endpoints from the '
          'GCP Console at')
    print('https://console.cloud.google.com/vertex-ai\n')

    if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ.keys():
        print('No application credentials found. Please make sure to set the '
              'GOOGLE_APPLICATION_CREDENTIALS')
        print('environment variable to a valid service account auth key.')
        exit()
    else:
        print('Using auth credentials from ' +
              os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

    dataset_types = [
        'ImageDataset', 'TabularDataset', 'TextDataset', 'TimeSeriesDataset',
        'VideoDataset'
    ]
    dataset_attrs = ['name', 'display_name']

    model_types = ['Model']
    model_attrs = ['name', 'display_name']

    job_types = [
        'AutoMLForecastingTrainingJob', 'AutoMLImageTrainingJob',
        'AutoMLTabularTrainingJob', 'AutoMLTextTrainingJob',
        'AutoMLVideoTrainingJob', 'BatchPredictionJob',
        'CustomContainerTrainingJob', 'CustomJob',
        'CustomPythonPackageTrainingJob', 'CustomTrainingJob',
        'HyperparameterTuningJob', 'PipelineJob'
    ]
    job_attrs = ['name', 'display_name', 'state.name']

    endpoint_types = ['Endpoint']
    endpoint_attrs = ['name', 'display_name']

    if args.datasets or args.all:
        list_objects(dataset_types, dataset_attrs)

    if args.models or args.all:
        list_objects(model_types, model_attrs)

    if args.jobs or args.all:
        list_objects(job_types, job_attrs)

    if args.endpoints or args.all:
        list_objects(endpoint_types, endpoint_attrs)

    if args.delete:
        delete_object(dataset_types + model_types + job_types + endpoint_types,
                      args.delete)


if __name__ == "__main__":
    main()
