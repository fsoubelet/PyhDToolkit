"""
Module models.htc
-----------------

Created on 2021.07.30
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with `pydantic` models to validate and store data obtained by querying the HTCondor queue.
"""
from typing import Union

from pendulum import DateTime
from pydantic import BaseModel


class BaseSummary(BaseModel):
    jobs: int
    completed: int
    removed: int
    idle: int
    running: int
    held: int
    suspended: int


class ClusterSummary(BaseModel):
    scheduler_id: str
    query: BaseSummary
    user: BaseSummary
    cluster: BaseSummary


class HTCTaskSummary(BaseModel):
    owner: str
    batch_name: int
    submitted: DateTime
    done: Union[int, str]
    run: Union[int, str]
    idle: Union[int, str]
    total: int
    job_ids: str
