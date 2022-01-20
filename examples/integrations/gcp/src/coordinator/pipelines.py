from etl.images.bounding_box_etl import BoundingBoxETL
from training.images.bounding_box_training_placeholder import BoundingBoxTraining

pipelines = {
    'bounding_box': {
        'etl': BoundingBoxETL(),
        'train': BoundingBoxTraining()
    }
}
