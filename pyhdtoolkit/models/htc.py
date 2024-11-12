"""
.. _models-htc:

HTCondor Models
---------------

Module with ``pydantic`` models to validate and store
data obtained by querying the ``HTCondor`` queue.
"""

from pendulum import DateTime
from pydantic import BaseModel, ConfigDict


class BaseSummary(BaseModel):
    """
    .. versionadded:: 0.12.0

    Class to encompass and validate the cluster's summary
    line in the ``condor_q`` output.
    """

    jobs: int
    completed: int
    removed: int
    idle: int
    running: int
    held: int
    suspended: int


class ClusterSummary(BaseModel):
    """
    .. versionadded:: 0.12.0

    Class to encompass and validate the cluster's info
    line in the ``condor_q`` output.
    """

    scheduler_id: str
    query: BaseSummary
    user: BaseSummary
    cluster: BaseSummary


class HTCTaskSummary(BaseModel):
    """
    .. versionadded:: 0.12.0

    Class to encompass and validate a specific job's line
    in the ``condor_q`` output.
    """

    # This is so pydantic accepts pendulum.DateTime as a validated type
    model_config = ConfigDict(arbitrary_types_allowed=True)

    owner: str
    batch_name: int
    submitted: DateTime
    done: int | str
    run: int | str
    idle: int | str
    total: int
    job_ids: str
