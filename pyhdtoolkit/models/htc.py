"""
.. _models-htc:

HTCondor Models
---------------

Module with ``pydantic`` models to validate and store data obtained by querying the ``HTCondor`` queue.
"""
from typing import Union

from pendulum import DateTime
from pydantic import BaseModel


class BaseSummary(BaseModel):
    """Class to encompass and validate the cluster's summary line in the ``condor_q`` output."""

    jobs: int
    completed: int
    removed: int
    idle: int
    running: int
    held: int
    suspended: int


class ClusterSummary(BaseModel):
    """Class to encompass and validate the cluster's info line in the ``condor_q`` output."""

    scheduler_id: str
    query: BaseSummary
    user: BaseSummary
    cluster: BaseSummary


class HTCTaskSummary(BaseModel):
    """Class to encompass and validate a specific job's line in the ``condor_q`` output."""

    owner: str
    batch_name: int
    submitted: DateTime
    done: Union[int, str]
    run: Union[int, str]
    idle: Union[int, str]
    total: int
    job_ids: str
