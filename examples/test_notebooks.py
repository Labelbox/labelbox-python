"""
Runs example notebooks to ensure that they are not throwing an error. 
"""

import pathlib
import pytest

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

examples_path = pathlib.Path(__file__).parent
notebook_paths = examples_path.glob('**/*.ipynb')
filtered_notebook_paths = [
    path for path in notebook_paths if '.ipynb_checkpoints' not in str(path)
]
relative_notebook_paths = [
    str(p.relative_to(examples_path)) for p in filtered_notebook_paths
]


def run_notebook(filename):
    with open(filename) as ff:
        nb_in = nbformat.read(ff, nbformat.NO_CONVERT)

    ep = ExecutePreprocessor(timeout=1200, kernel_name='python3')

    ep.preprocess(nb_in)


SKIP_LIST = [
    'extras/classification-confusion-matrix.ipynb',
    'label_export/images.ipynb',
    'label_export/text.ipynb',
    'label_export/video.ipynb',
    'annotation_types/converters.ipynb',
    'integrations/detectron2/coco_panoptic.ipynb',
    'integrations/tlt/detectnet_v2_bounding_box.ipynb',
    'basics/datasets.ipynb',
    'basics/data_rows.ipynb',
    'basics/labels.ipynb',
    'basics/data_row_metadata.ipynb',
    'model_diagnostics/custom_metrics_basics.ipynb',
    'basics/user_management.ipynb',
    'integrations/tlt/labelbox_upload.ipynb',
    'model_diagnostics/custom_metrics_demo.ipynb',
    'model_diagnostics/model_diagnostics_demo.ipynb',
    'integrations/databricks/',
    'integrations/detectron2/coco_object.ipynb',
    'project_configuration/webhooks.ipynb',
    'basics/projects.ipynb',
    'model_diagnostics/model_diagnostics_guide.ipynb',
]


def skip_notebook(notebook_path):
    for skip_path in SKIP_LIST:
        if notebook_path.startswith(skip_path):
            return True
    return False


run_notebook_paths = [
    path for path in relative_notebook_paths if not skip_notebook(path)
]


@pytest.mark.skip(
    'Need some more work to run reliably, e.g. figuring out how to deal with '
    'max number of models per org, therefore skipping from CI. However, this '
    'test can be run locally after updating notebooks to ensure notebooks '
    'are working.')
@pytest.mark.parametrize("notebook_path", run_notebook_paths)
def test_notebooks_run_without_errors(notebook_path):
    run_notebook(examples_path / notebook_path)
