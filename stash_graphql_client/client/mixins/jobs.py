"""Job operations client functionality."""

import asyncio
import time

from ... import fragments
from ...types import FindJobInput, Job, JobStatus
from ..protocols import StashClientProtocol


class JobsClientMixin(StashClientProtocol):
    """Mixin for job-related client methods."""

    async def find_job(self, job_id: str) -> Job | None:
        """Find a job by ID.

        Args:
            job_id: Job ID to find

        Returns:
            Job object if found, None otherwise

        Examples:
            Find a job and check its status:
            ```python
            job = await client.find_job("123")
            if job:
                print(f"Job status: {job.status}")
            ```
        """
        if not job_id:
            return None

        try:
            result = await self.execute(
                fragments.FIND_JOB_QUERY,
                {"input": FindJobInput(id=job_id).__dict__},
            )
            # First check if there are any GraphQL errors
            if "errors" in result:
                return None
            # Then check if we got a valid job back
            if job_data := result.get("findJob"):
                return Job(**job_data)
            return None
        except Exception as e:
            self.log.error(f"Failed to find job {job_id}: {e}")
            return None

    async def wait_for_job(
        self,
        job_id: str | int,
        status: JobStatus = JobStatus.FINISHED,
        period: float = 1.5,
        timeout: float = 120.0,
    ) -> bool | None:
        """Wait for a job to reach a specific status.

        Args:
            job_id: Job ID to wait for
            status: Status to wait for (default: JobStatus.FINISHED)
            period: Time between checks in seconds (default: 1.5)
            timeout: Maximum time to wait in seconds (default: 120)

        Returns:
            True if job reached desired status
            False if job finished with different status
            None if job not found

        Raises:
            TimeoutError: If timeout is reached
            ValueError: If job is not found
        """
        if not job_id:
            return None

        timeout_value = time.time() + timeout
        while time.time() < timeout_value:
            job = await self.find_job(str(job_id))
            if not isinstance(job, Job):
                raise ValueError(f"Job {job_id} not found")

            # Only log through stash's logger
            self.log.info(
                f"Job {job_id} - Status: {job.status}, Progress: {job.progress}%"
            )

            # Check for desired state
            if job.status == status:
                return True
            if job.status in [JobStatus.FINISHED, JobStatus.CANCELLED]:
                return False

            await asyncio.sleep(period)

        raise TimeoutError(f"Timeout waiting for job {job_id} to reach status {status}")

    async def stop_job(self, job_id: str) -> bool:
        """Stop a specific job.

        Args:
            job_id: Job ID to stop

        Returns:
            True if job was stopped successfully, False otherwise

        Examples:
            Stop a running job:
            ```python
            job_id = await client.metadata_generate(...)
            success = await client.stop_job(job_id)
            if success:
                print(f"Job {job_id} stopped")
            ```
        """
        try:
            result = await self.execute(
                """
                mutation StopJob($job_id: ID!) {
                    stopJob(job_id: $job_id)
                }
                """,
                {"job_id": job_id},
            )
            return bool(result.get("stopJob", False))
        except Exception as e:
            self.log.error(f"Failed to stop job {job_id}: {e}")
            return False

    async def stop_all_jobs(self) -> bool:
        """Stop all running jobs.

        Returns:
            True if all jobs were stopped successfully, False otherwise

        Examples:
            Stop all running jobs:
            ```python
            success = await client.stop_all_jobs()
            if success:
                print("All jobs stopped")
            ```
        """
        try:
            result = await self.execute(
                """
                mutation StopAllJobs {
                    stopAllJobs
                }
                """
            )
            return bool(result.get("stopAllJobs", False))
        except Exception as e:
            self.log.error(f"Failed to stop all jobs: {e}")
            return False

    async def job_queue(self) -> list[Job]:
        """Get all jobs in the queue.

        Returns:
            List of Job objects representing all jobs (running, pending, finished)

        Examples:
            Get all jobs:
            ```python
            jobs = await client.job_queue()
            for job in jobs:
                print(f"Job {job.id}: {job.status} - {job.description}")
            ```

            Filter by status:
            ```python
            jobs = await client.job_queue()
            running = [j for j in jobs if j.status == JobStatus.RUNNING]
            print(f"Running jobs: {len(running)}")
            ```
        """
        try:
            result = await self.execute(
                """
                query JobQueue {
                    jobQueue {
                        id
                        status
                        subTasks
                        description
                        progress
                        startTime
                        endTime
                        addTime
                        error
                    }
                }
                """
            )
            job_data_list = result.get("jobQueue", [])
            return [Job(**job_data) for job_data in job_data_list]
        except Exception as e:
            self.log.error(f"Failed to get job queue: {e}")
            return []
