"""
Tools for grouping features and labels so that we can compute metrics on the individual groups
"""

from collections import defaultdict
from typing import Dict, List, Tuple, Union

from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import (
    Checklist,
    ClassificationAnswer,
    Radio,
    Text,
)

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ..annotation_types.feature import FeatureSchema
from ..annotation_types import ObjectAnnotation, ClassificationAnnotation, Label


def get_identifying_key(
    features_a: List[FeatureSchema], features_b: List[FeatureSchema]
) -> Union[Literal["name"], Literal["feature_schema_id"]]:
    """
    Checks to make sure that features in both sets contain the same type of identifying keys.
    This can either be the feature name or feature schema id.

    Args:
        features_a : List of FeatureSchemas (usually ObjectAnnotations or ClassificationAnnotations)
        features_b : List of FeatureSchemas (usually ObjectAnnotations or ClassificationAnnotations)
    Returns:
        The field name that is present in both feature lists.
    """

    all_schema_ids_defined_pred, all_names_defined_pred = all_have_key(
        features_a
    )
    if not all_schema_ids_defined_pred and not all_names_defined_pred:
        raise ValueError("All data must have feature_schema_ids or names set")

    all_schema_ids_defined_gt, all_names_defined_gt = all_have_key(features_b)

    # Prefer name becuse the user will be able to know what it means
    # Schema id incase that doesn't exist.
    if all_names_defined_pred and all_names_defined_gt:
        return "name"
    elif all_schema_ids_defined_pred and all_schema_ids_defined_gt:
        return "feature_schema_id"
    else:
        raise ValueError(
            "Ground truth and prediction annotations must have set all name or feature ids. "
            "Otherwise there is no key to match on. Please update."
        )


def all_have_key(features: List[FeatureSchema]) -> Tuple[bool, bool]:
    """
    Checks to make sure that all FeatureSchemas have names set or feature_schema_ids set.

    Args:
        features (List[FeatureSchema]) :

    """
    all_names = True
    all_schemas = True
    for feature in features:
        if isinstance(feature, ClassificationAnnotation):
            if isinstance(feature.value, Checklist):
                all_schemas, all_names = all_have_key(feature.value.answer)
            elif isinstance(feature.value, Text):
                if feature.name is None:
                    all_names = False
                if feature.feature_schema_id is None:
                    all_schemas = False
            else:
                if feature.value.answer.name is None:
                    all_names = False
                if feature.value.answer.feature_schema_id is None:
                    all_schemas = False
        if feature.name is None:
            all_names = False
        if feature.feature_schema_id is None:
            all_schemas = False
    return all_schemas, all_names


def get_label_pairs(
    labels_a: list, labels_b: list, match_on="uid", filter_mismatch=False
) -> Dict[str, Tuple[Label, Label]]:
    """
    This is a function to pairing a list of prediction labels and a list of ground truth labels easier.
    There are a few potentiall problems with this function.
    We are assuming that the data row `uid` or `external id` have been provided by the user.
    However, these particular fields are not required and can be empty.
    If this assumption fails, then the user has to determine their own matching strategy.

    Args:
        labels_a (list): A collection of labels to match with labels_b
        labels_b (list): A collection of labels to match with labels_a
        match_on ('uid' or 'external_id'): The data row key to match labels by. Can either be uid or external id.
        filter_mismatch (bool): Whether or not to ignore mismatches

    Returns:
        A dict containing the union of all either uids or external ids and values as a tuple of the matched labels

    """

    if match_on not in ["uid", "external_id"]:
        raise ValueError("Can only match on  `uid` or `exteranl_id`.")

    label_lookup_a = {
        getattr(label.data, match_on, None): label for label in labels_a
    }
    label_lookup_b = {
        getattr(label.data, match_on, None): label for label in labels_b
    }
    all_keys = set(label_lookup_a.keys()).union(label_lookup_b.keys())
    if None in label_lookup_a or None in label_lookup_b:
        raise ValueError(
            f"One or more of the labels has a data row without the required key {match_on}."
            " It cannot be determined which labels match without this information."
            f" Either assign {match_on} to each Label or create your own pairing function."
        )
    pairs = defaultdict(list)
    for key in all_keys:
        a, b = label_lookup_a.pop(key, None), label_lookup_b.pop(key, None)
        if a is None or b is None:
            if not filter_mismatch:
                raise ValueError(
                    f"{match_on} {key} is not available in both LabelLists. "
                    "Set `filter_mismatch = True` to filter out these examples, assign the ids manually, or create your own matching function."
                )
            else:
                continue
        pairs[key].extend([a, b])
    return pairs


def get_feature_pairs(
    features_a: List[FeatureSchema], features_b: List[FeatureSchema]
) -> Dict[str, Tuple[List[FeatureSchema], List[FeatureSchema]]]:
    """
    Matches features by schema_ids

    Args:
        labels_a (List[FeatureSchema]): A list of features to match with features_b
        labels_b (List[FeatureSchema]): A list of features to match with features_a
    Returns:
        The matched features as dict. The key will be the feature name and the value will be
        two lists each containing the matched features from each set.

    """
    identifying_key = get_identifying_key(features_a, features_b)
    lookup_a, lookup_b = (
        _create_feature_lookup(features_a, identifying_key),
        _create_feature_lookup(features_b, identifying_key),
    )

    keys = set(lookup_a.keys()).union(set(lookup_b.keys()))
    result = defaultdict(list)
    for key in keys:
        result[key].extend([lookup_a[key], lookup_b[key]])
    return result


def _create_feature_lookup(
    features: List[FeatureSchema], key: str
) -> Dict[str, List[FeatureSchema]]:
    """
    Groups annotation by name (if available otherwise feature schema id).

    Args:
        annotations: List of annotations to group
    Returns:
        a dict where each key is the feature_schema_id (or name)
        and the value is a list of annotations that have that feature_schema_id (or name)
    """
    grouped_features = defaultdict(list)
    for feature in features:
        if isinstance(feature, ClassificationAnnotation):
            # checklists
            if isinstance(feature.value, Checklist):
                for answer in feature.value.answer:
                    new_answer = Radio(answer=answer)
                    new_annotation = ClassificationAnnotation(
                        value=new_answer,
                        name=answer.name,
                        feature_schema_id=answer.feature_schema_id,
                    )

                    grouped_features[getattr(answer, key)].append(
                        new_annotation
                    )
            elif isinstance(feature.value, Text):
                grouped_features[getattr(feature, key)].append(feature)
            else:
                grouped_features[getattr(feature.value.answer, key)].append(
                    feature
                )
        else:
            grouped_features[getattr(feature, key)].append(feature)
    return grouped_features


def has_no_matching_annotations(
    ground_truths: List[ObjectAnnotation], predictions: List[ObjectAnnotation]
):
    if len(ground_truths) and not len(predictions):
        # No existing predictions but existing ground truths means no matches.
        return True
    elif not len(ground_truths) and len(predictions):
        # No ground truth annotations but there are predictions means no matches
        return True
    return False


def has_no_annotations(
    ground_truths: List[ObjectAnnotation], predictions: List[ObjectAnnotation]
):
    return not len(ground_truths) and not len(predictions)
