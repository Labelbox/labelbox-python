## Labelbox SDK Examples

- Learn how to use the SDK by following along
- Run in google colab, view the notebooks on github, or clone the repo and run locally

---

## [Basics](basics)

| Notebook          | Github                                   | Google Colab                                                                                                                                                                                        |
| ----------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fundamentals      | [Github](basics/basics.ipynb)            | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/basics.ipynb)            |
| Batches           | [Github](basics/batches.ipynb)           | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/batches.ipynb)           |
| Data Rows         | [Github](basics/data_rows.ipynb)         | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/data_rows.ipynb)         |
| Data Row Metadata | [Github](basics/data_row_metadata.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/data_row_metadata.ipynb) |
| Datasets          | [Github](basics/datasets.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/datasets.ipynb)          |
| Export data       | [Github](basics/export_data.ipynb)       | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/export_data.ipynb)       |
| Ontologies        | [Github](basics/ontologies.ipynb)        | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/ontologies.ipynb)        |
| Projects          | [Github](basics/projects.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/projects.ipynb)          |
| User Management   | [Github](basics/user_management.ipynb)   | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/basics/user_management.ipynb)   |

---

## [Model Training](https://docs.labelbox.com/docs/integration-with-model-training-service)

Train a model using data annotated on Labelbox

| Notebook                        | Github                                                | Google Colab                                                                                                                                                                                                     |
| ------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Object Detection (Detectron2)   | [Github](integrations/detectron2/coco_object.ipynb)   | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/integrations/detectron2/coco_object.ipynb)   |
| Panoptic Detection (Detectron2) | [Github](integrations/detectron2/coco_panoptic.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/integrations/detectron2/coco_panoptic.ipynb) |

---

## [Annotation Import (Ground Truth & MAL)](annotation_import)

| Notebook                              | Github                                           | Google Colab                                                                                                                                                                                                | Learn more                                                                         |
| ------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Image Annotation Import               | [Github](annotation_import/image.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/image.ipynb)          | [Docs](https://docs.labelbox.com/reference/import-image-annotations)               |
| Text Annotation Import                | [Github](annotation_import/text.ipynb)           | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/text.ipynb)           | [Docs](https://docs.labelbox.com/reference/import-text-annotations)                |
| Tiled Imagery Annotation Import       | [Github](annotation_import/tiled.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/tiled.ipynb)          | [Docs](https://docs.labelbox.com/reference/import-geospatial-annotations)          |
| Video Annotation Import               | [Github](annotation_import/video.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/video.ipynb)          | [Docs](https://docs.labelbox.com/reference/import-video-annotations)               |
| PDF Annotation Import                 | [Github](annotation_import/pdf.ipynb)            | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/pdf.ipynb)            | [Docs](https://docs.labelbox.com/reference/import-document-annotations)            |
| Audio Annotation Import               | [Github](annotation_import/audio.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/audio.ipynb)          | [Docs](https://docs.labelbox.com/reference/import-audio-annotations)               |
| HTML Annotation Import                | [Github](annotation_import/html.ipynb)           | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/html.ipynb)           | [Docs](https://docs.labelbox.com/reference/import-html-annotations)                |
| DICOM Annotation Import               | [Github](annotation_import/dicom.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/dicom.ipynb)          | [Docs](https://docs.labelbox.com/reference/import-dicom-annotations)               |
| Conversational Text Annotation Import | [Github](annotation_import/conversational.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/annotation_import/conversational.ipynb) | [Docs](https://docs.labelbox.com/reference/import-conversational-text-annotations) |

---

## [Project Configuration](project_configuration)

| Notebook         | Github                                                 | Google Colab                                                                                                                                                                                                      |
| ---------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Project Setup    | [Github](project_configuration/project_setup.ipynb)    | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/project_configuration/project_setup.ipynb)    |
| Queue Management | [Github](project_configuration/queue_management.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/project_configuration/queue_management.ipynb) |
| Webhooks         | [Github](project_configuration/webhooks.ipynb)         | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/project_configuration/webhooks.ipynb)         |

## [Prediction Upload to a Model Run](prediction_upload)

| Notebook                              | Github                                                       | Google Colab                                                                                                                                                                                                            | Learn more                                                                |
| ------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Image Prediction upload               | [Github](prediction_upload/image_predictions.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/prediction_upload/image_predictions.ipynb)          | [Docs](https://docs.labelbox.com/reference/upload-image-predictions)      |
| Text Prediction upload                | [Github](prediction_upload/text_predictions.ipynb)           | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/prediction_upload/text_predictions.ipynb)           | [Docs](https://docs.labelbox.com/reference/upload-text-predictions)       |
| Video Prediction upload               | [Github](prediction_upload/video_predictions.ipynb)          | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/prediction_upload/video_predictions.ipynb)          | [Docs](https://docs.labelbox.com/reference/upload-video-predictions)      |
| HTML Prediction upload                | [Github](prediction_upload/html_predictions.ipynb)           | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/prediction_upload/html_predictions.ipynb)           | [Docs](https://docs.labelbox.com/reference/upload-html-predictions)       |
| PDF Prediction upload                 | [Github](prediction_upload/pdf_predictions.ipynb)            | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/prediction_upload/pdf_predictions.ipynb)            |
| Geospatial Prediction upload          | [Github](prediction_upload/geospatial_predictions.ipynb)     | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/prediction_upload/geospatial_predictions.ipynb)     | [Docs](https://docs.labelbox.com/reference/upload-geospatial-predictions) |
| Conversational Text Prediction upload | [Github](prediction_upload/conversational_predictions.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/prediction_upload/conversational_predictions.ipynb) |

---

## [Extras](extras)

| Notebook                        | Github                                                 | Google Colab                                                                                                                                                                                                      |
| ------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Classification Confusion Matrix | [Github](extras/classification-confusion-matrix.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Labelbox/labelbox-python/blob/master/examples/extras/classification-confusion-matrix.ipynb) |
