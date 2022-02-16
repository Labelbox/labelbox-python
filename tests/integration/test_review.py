import pytest

from labelbox import Review
from labelbox.exceptions import InvalidQueryError


def test_reviews(configured_project_with_label):
    _, _, _, label = configured_project_with_label

    assert set(label.reviews()) == set()

    r1 = label.create_review(score=-1.0)
    # They work on data that was created in the editor but not with project.create_label
    # assert r1.project() == project
    # assert r1.label() == label
    assert r1.score == -1.0
    assert set(label.reviews()) == {r1}

    r2 = label.create_review(score=1.0)

    assert set(label.reviews()) == {r1, r2}

    # Label.reviews doesn't support filtering
    with pytest.raises(InvalidQueryError) as exc_info:
        assert set(label.reviews(where=Review.score > 0.0)) == {r2}
    assert exc_info.value.message == \
        "Relationship Label.reviews doesn't support filtering"

    r1.delete()

    assert set(label.reviews()) == {r2}


def test_review_metrics(configured_project_with_label):
    project, _, _, _ = configured_project_with_label

    assert project.review_metrics(None) == 1
    assert project.review_metrics(Review.NetScore.Negative) == 0
    assert project.review_metrics(Review.NetScore.Zero) == 0
    assert project.review_metrics(Review.NetScore.Positive) == 0

    for count, score in ((4, 0), (2, 1), (3, -1)):
        for _ in range(count):
            project.create_label()
            next(project.labels()).create_review(score=score)

    assert project.review_metrics(None) == 1
    assert project.review_metrics(Review.NetScore.Negative) == 3
    assert project.review_metrics(Review.NetScore.Zero) == 4
    assert project.review_metrics(Review.NetScore.Positive) == 2

    with pytest.raises(InvalidQueryError):
        project.review_metrics(12)
