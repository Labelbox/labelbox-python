from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AutoQaStatus(str, Enum):
    Approve = "Approve"
    Reject = "Reject"
    Neutral = "Neutral"


class SubmittedBy(BaseModel):
    email: str


class CustomScore(BaseModel):
    name: str
    value: float


class AutoQA(BaseModel):
    status: AutoQaStatus
    score: Optional[float] = None
    feedback: Optional[str] = None
    custom_scores: Optional[List[CustomScore]] = None


class ProjectSyncLabel(BaseModel):
    submitted_by: SubmittedBy
    auto_qa: Optional[AutoQA] = None
    seconds_to_completion: Optional[float] = None
    submitted_on: Optional[str] = None


class ReviewedBy(BaseModel):
    email: str


class GranularRating(BaseModel):
    score: int
    comment: Optional[str] = None


class ProjectSyncReview(BaseModel):
    reviewed_by: ReviewedBy
    rating: Optional[GranularRating] = None
    custom_scores: Optional[List[CustomScore]] = None


class ProjectSyncEntry(BaseModel):
    task_id: str
    content_url: Optional[str] = None
    label: Optional[ProjectSyncLabel] = None
    review: Optional[ProjectSyncReview] = None
    queue_type: Optional[str] = None


class ProjectSyncResult(BaseModel):
    submission_id: str


def _to_gql_input(entry: ProjectSyncEntry) -> Dict[str, Any]:
    """Convert a ProjectSyncEntry to a camelCase dict matching the GQL schema."""
    result: Dict[str, Any] = {"taskId": entry.task_id}

    if entry.content_url is not None:
        result["contentUrl"] = entry.content_url

    if entry.label is not None:
        label: Dict[str, Any] = {
            "submittedBy": {"email": entry.label.submitted_by.email},
        }

        if entry.label.auto_qa is not None:
            auto_qa: Dict[str, Any] = {
                "status": entry.label.auto_qa.status.value,
            }
            if entry.label.auto_qa.score is not None:
                auto_qa["score"] = entry.label.auto_qa.score
            if entry.label.auto_qa.feedback is not None:
                auto_qa["feedback"] = entry.label.auto_qa.feedback
            if entry.label.auto_qa.custom_scores is not None:
                auto_qa["customScores"] = [
                    {"name": cs.name, "value": cs.value}
                    for cs in entry.label.auto_qa.custom_scores
                ]
            label["autoQA"] = auto_qa

        if entry.label.seconds_to_completion is not None:
            label["secondsToCompletion"] = entry.label.seconds_to_completion

        if entry.label.submitted_on is not None:
            label["submittedOn"] = entry.label.submitted_on

        result["label"] = label
    elif "label" in entry.model_fields_set:
        result["label"] = None

    if entry.review is not None:
        review: Dict[str, Any] = {
            "reviewedBy": {"email": entry.review.reviewed_by.email},
        }
        if entry.review.rating is not None:
            rating: Dict[str, Any] = {"score": entry.review.rating.score}
            if entry.review.rating.comment is not None:
                rating["comment"] = entry.review.rating.comment
            review["rating"] = rating
        if entry.review.custom_scores is not None:
            review["customScores"] = [
                {"name": cs.name, "value": cs.value}
                for cs in entry.review.custom_scores
            ]
        result["review"] = review

    if entry.queue_type is not None:
        result["queueType"] = entry.queue_type
    elif "queue_type" in entry.model_fields_set:
        result["queueType"] = None

    return result
