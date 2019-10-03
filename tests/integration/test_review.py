import pytest

from labelbox import Review
from labelbox.exceptions import InvalidQueryError


IMG_URL = "https://picsum.photos/200/300"


def test_reviews(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    label = project.create_label(data_row=data_row, label="test",
                                 seconds_to_label=0.0)

    assert set(label.reviews()) == set()
    assert set(project.reviews()) == set()

    r1 = label.create_review(score=-1.0)
    assert r1.project() == project
    assert r1.label() == label
    assert r1.score == -1.0
    assert set(label.reviews()) == {r1}
    assert set(project.reviews()) == {r1}

    r2 = label.create_review(score=1.0)

    assert set(label.reviews()) == {r1, r2}
    assert set(project.reviews()) == {r1, r2}

    # Project.reviews supports filtering
    assert set(project.reviews(where=Review.score > 0.0)) == {r2}
    assert set(project.reviews(where=Review.score < 0.0)) == {r1}

    # Label.reviews doesn't support filtering
    with pytest.raises(InvalidQueryError) as exc_info:
        assert set(label.reviews(where=Review.score > 0.0)) == {r2}
    assert exc_info.value.message == \
        "Relationship Label.reviews doesn't support filtering"

    r1.delete()

    assert set(label.reviews()) == {r2}
    assert set(project.reviews()) == {r2}

    dataset.delete()
    project.delete()


def test_review_metrics(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    label = project.create_label(data_row=data_row, label="test",
                                 seconds_to_label=0.0)

    assert project.review_metrics(None) == 1
    assert project.review_metrics(Review.NetScore.Negative) == 0
    assert project.review_metrics(Review.NetScore.Zero) == 0
    assert project.review_metrics(Review.NetScore.Positive) == 0

    for count, score in ((4, 0), (2, 1), (3, -1)):
        for _ in range(count):
            l = project.create_label(data_row=data_row, label="l",
                                     seconds_to_label=0.0)
            l.create_review(score=score)

    assert project.review_metrics(None) == 1
    assert project.review_metrics(Review.NetScore.Negative) == 3
    assert project.review_metrics(Review.NetScore.Zero) == 4
    assert project.review_metrics(Review.NetScore.Positive) == 2

    with pytest.raises(InvalidQueryError):
        project.review_metrics(12)

    dataset.delete()
    project.delete()
