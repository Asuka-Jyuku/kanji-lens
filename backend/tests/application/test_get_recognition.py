import pytest

from fakes import DRAWING, T0, FakeJobRepository
from kanjilens.application.use_cases.get_recognition import GetRecognition
from kanjilens.domain.errors import JobNotFound
from kanjilens.domain.job import RecognitionJob
from kanjilens.domain.stroke_order import StrokeOrderMode


def test_a_stored_job_is_returned_as_it_is() -> None:
    repository = FakeJobRepository()
    job = RecognitionJob.submit(mode=StrokeOrderMode.ORDERED, drawing=DRAWING, now=T0)
    repository.save(job)

    assert GetRecognition(repository).execute(job.id) == job


def test_a_missing_or_expired_job_is_job_not_found() -> None:
    # The repository answers None for both (the in-memory one drops expired jobs).
    with pytest.raises(JobNotFound) as error:
        GetRecognition(FakeJobRepository()).execute("nothing-here")

    assert error.value.code == "job_not_found"
