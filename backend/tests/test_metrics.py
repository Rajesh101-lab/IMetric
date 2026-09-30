import pytest
from app.services.metrics import compute_metrics


def test_compute_metrics_empty_reels():
    res = compute_metrics(followers=1000, reels=[], username="testpage")
    assert res.username == "testpage"
    assert res.followers == 1000
    assert res.lastreellikes is None
    assert res.lastreelviews is None
    assert res.avgviews == 0.0
    assert res.medianviews == 0.0
    assert res.avglikes == 0.0
    assert res.liketoviewratio == 0.0
    assert res.avgviewsperfollower == 0.0
    assert res.reelssampled == 0


def test_compute_metrics_zero_followers():
    reels = [{"views": 100, "likes": 10}]
    res = compute_metrics(followers=0, reels=reels, username="zerofollowers")
    assert res.avgviews == 100.0
    assert res.avgviewsperfollower == 0.0
    assert res.liketoviewratio == 0.1


def test_compute_metrics_zero_views():
    reels = [{"views": 0, "likes": 0}, {"views": 0, "likes": 0}]
    res = compute_metrics(followers=500, reels=reels, username="zeroviews")
    assert res.avgviews == 0.0
    assert res.liketoviewratio == 0.0
    assert res.avgviewsperfollower == 0.0


def test_compute_metrics_odd_sample_median():
    reels = [
        {"views": 100, "likes": 10},
        {"views": 300, "likes": 30},
        {"views": 200, "likes": 20},
    ]
    res = compute_metrics(followers=1000, reels=reels, username="oddpage")
    assert res.avgviews == 200.0
    assert res.medianviews == 200.0
    assert res.avglikes == 20.0
    assert res.liketoviewratio == 0.1
    assert res.lastreelviews == 100
    assert res.lastreellikes == 10
    assert res.reelssampled == 3


def test_compute_metrics_even_sample_median():
    reels = [
        {"views": 100, "likes": 10},
        {"views": 200, "likes": 20},
        {"views": 300, "likes": 30},
        {"views": 400, "likes": 40},
    ]
    res = compute_metrics(followers=1000, reels=reels, username="evenpage")
    assert res.avgviews == 250.0
    assert res.medianviews == 250.0  # Mean of 200 and 300
    assert res.avglikes == 25.0
    assert res.liketoviewratio == 0.1
    assert res.reelssampled == 4


def test_compute_metrics_sample_capping():
    # 20 reels provided, sample size 12
    reels = [{"views": i * 10, "likes": i} for i in range(1, 21)]
    res = compute_metrics(followers=1000, reels=reels, username="cappeage", sample_size=12)
    assert res.reelssampled == 12
