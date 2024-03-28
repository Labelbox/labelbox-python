import json

import pytest

import labelbox as lb
import labelbox.types as lb_types
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.schema.annotation_import import AnnotationImportState
from labelbox.schema.export_task import ExportTask, StreamType


class TestExportVideo:

    @pytest.fixture
    def user_id(self, client):
        return client.get_user().uid

    @pytest.fixture
    def org_id(self, client):
        return client.get_organization().uid

    def test_export(
        self,
        client,
        configured_project_without_data_rows,
        video_data,
        video_data_row,
        bbox_video_annotation_objects,
        rand_gen,
    ):
        project = configured_project_without_data_rows
        project_id = project.uid
        labels = []

        _, data_row_uids = video_data
        project.create_batch(
            rand_gen(str),
            data_row_uids,  # sample of data row objects
            5,  # priority between 1(Highest) - 5(lowest)
        )

        for data_row_uid in data_row_uids:
            labels = [
                lb_types.Label(data=VideoData(uid=data_row_uid),
                               annotations=bbox_video_annotation_objects)
            ]

        label_import = lb.LabelImport.create_from_objects(
            client, project_id, f"test-import-{project_id}", labels)
        label_import.wait_until_done()

        assert label_import.state == AnnotationImportState.FINISHED
        assert len(label_import.errors) == 0

        export_task = project.export(
            params={
                "performance_details": False,
                "label_details": True,
                "interpolated_frames": True,
            },
            task_name="TestExportVideo:test_export",
        )
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0

        export_data = json.loads(list(export_task.get_stream())[0].json_str)
        data_row_export = export_data["data_row"]
        assert data_row_export["global_key"] == video_data_row["global_key"]
        assert data_row_export["row_data"] == video_data_row["row_data"]
        assert export_data["media_attributes"]["mime_type"] == "video/mp4"
        assert export_data["media_attributes"][
            "frame_rate"] == 10  # as per the video_data fixture
        assert (export_data["media_attributes"]["frame_count"] == 100
               )  # as per the video_data fixture
        expected_export_label = {
            "label_kind": "Video",
            "version": "1.0.0",
            "id": "clgjnpysl000xi3zxtnp29fug",
            "label_details": {
                "created_at": "2023-04-16T17:04:23+00:00",
                "updated_at": "2023-04-16T17:04:23+00:00",
                "created_by": "vbrodsky@labelbox.com",
                "content_last_updated_at": "2023-04-16T17:04:23+00:00",
                "reviews": [],
            },
            "annotations": {
                "frames": {
                    "13": {
                        "objects": {
                            "clgjnpyse000ui3zx6fr1d880": {
                                "feature_id": "clgjnpyse000ui3zx6fr1d880",
                                "name": "bbox",
                                "annotation_kind": "VideoBoundingBox",
                                "classifications": [{
                                    "feature_id": "clgjnpyse000vi3zxtgtfh01y",
                                    "name": "nested",
                                    "radio_answer": {
                                        "feature_id":
                                            "clgjnpyse000wi3zxnxgv53ps",
                                        "name":
                                            "radio_option_1",
                                        "classifications": [],
                                    },
                                }],
                                "bounding_box": {
                                    "top": 98.0,
                                    "left": 146.0,
                                    "height": 243.0,
                                    "width": 236.0,
                                },
                            }
                        },
                        "classifications": [],
                    },
                    "18": {
                        "objects": {
                            "clgjnpyse000ui3zx6fr1d880": {
                                "feature_id": "clgjnpyse000ui3zx6fr1d880",
                                "name": "bbox",
                                "annotation_kind": "VideoBoundingBox",
                                "classifications": [{
                                    "feature_id": "clgjnpyse000vi3zxtgtfh01y",
                                    "name": "nested",
                                    "radio_answer": {
                                        "feature_id":
                                            "clgjnpyse000wi3zxnxgv53ps",
                                        "name":
                                            "radio_option_1",
                                        "classifications": [],
                                    },
                                }],
                                "bounding_box": {
                                    "top": 98.0,
                                    "left": 146.0,
                                    "height": 243.0,
                                    "width": 236.0,
                                },
                            }
                        },
                        "classifications": [],
                    },
                    "19": {
                        "objects": {
                            "clgjnpyse000ui3zx6fr1d880": {
                                "feature_id": "clgjnpyse000ui3zx6fr1d880",
                                "name": "bbox",
                                "annotation_kind": "VideoBoundingBox",
                                "classifications": [],
                                "bounding_box": {
                                    "top": 98.0,
                                    "left": 146.0,
                                    "height": 243.0,
                                    "width": 236.0,
                                },
                            }
                        },
                        "classifications": [],
                    },
                },
                "segments": {
                    "clgjnpyse000ui3zx6fr1d880": [[13, 13], [18, 19]]
                },
                "key_frame_feature_map": {
                    "clgjnpyse000ui3zx6fr1d880": {
                        "13": True,
                        "18": False,
                        "19": True
                    }
                },
                "classifications": [],
            },
        }

        project_export_labels = export_data["projects"][project_id]["labels"]
        assert len(project_export_labels) == len(
            labels
        )  # note we create 1 label per data row, 1 data row so 1 label
        export_label = project_export_labels[0]
        assert (export_label["label_kind"]) == "Video"

        assert (export_label["label_details"].keys()
               ) == expected_export_label["label_details"].keys()

        expected_frames_ids = [
            vannotation.frame for vannotation in bbox_video_annotation_objects
        ]
        export_annotations = export_label["annotations"]
        export_frames = export_annotations["frames"]
        export_frames_ids = [int(frame_id) for frame_id in export_frames.keys()]
        all_frames_exported = []
        for (value) in (
                expected_frames_ids
        ):  # note need to understand why we are exporting more frames than we created
            if value not in export_frames_ids:
                all_frames_exported.append(value)
        assert len(all_frames_exported) == 0

        # BEGINNING OF THE VIDEO INTERPOLATION ASSERTIONS
        first_frame_id = bbox_video_annotation_objects[0].frame
        last_frame_id = bbox_video_annotation_objects[-1].frame

        # Generate list of frames with frames in between, e.g. 13, 14, 15, 16, 17, 18, 19
        expected_frame_ids = list(range(first_frame_id, last_frame_id + 1))

        assert export_frames_ids == expected_frame_ids

        exported_objects_dict = export_frames[str(first_frame_id)]["objects"]

        # Get the label ID
        first_exported_label_id = list(exported_objects_dict.keys())[0]

        # Since the bounding box moves to the right, the interpolated frame content should start
        # a little bit more far to the right
        assert (export_frames[str(first_frame_id + 1)]["objects"]
                [first_exported_label_id]["bounding_box"]["left"]
                > export_frames[str(first_frame_id)]["objects"]
                [first_exported_label_id]["bounding_box"]["left"])
        # But it shouldn't be further than the last frame
        assert (export_frames[str(first_frame_id + 1)]["objects"]
                [first_exported_label_id]["bounding_box"]["left"]
                < export_frames[str(last_frame_id)]["objects"]
                [first_exported_label_id]["bounding_box"]["left"])
        # END OF THE VIDEO INTERPOLATION ASSERTIONS

        frame_with_nested_classifications = export_frames["13"]
        annotation = None
        for _, a in frame_with_nested_classifications["objects"].items():
            if a["name"] == "bbox":
                annotation = a
                break
        assert annotation is not None
        assert annotation["annotation_kind"] == "VideoBoundingBox"
        assert annotation["classifications"]
        assert annotation["bounding_box"] == {
            "top": 98.0,
            "left": 146.0,
            "height": 243.0,
            "width": 236.0,
        }
        classifications = annotation["classifications"]
        classification = classifications[0]["radio_answer"]
        assert classification["name"] == "radio_option_1"
        subclassifications = classification["classifications"]
        # NOTE predictions services does not support nested classifications at the moment, see
        # https://labelbox.atlassian.net/browse/AL-5588
        assert len(subclassifications) == 0
