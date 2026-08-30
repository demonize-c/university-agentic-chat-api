# services/embedding_job_service.py

from datetime import datetime, timezone

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from python_university_support_agent.models import EmbeddingJob, JobStatus, Document


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------

async def create_job(
    db: AsyncSession,
    document_id: int,
    commit: bool = True,
) -> EmbeddingJob:
    """
    Create a new embedding job in QUEUED state.

    Call this when the embedding job is successfully queued.
    """

    document = await db.get(Document, document_id)

    if document is None:
        raise ValueError(
            f"Document {document_id} not found"
        )

    job = EmbeddingJob(
        document_id=document_id,
        status=JobStatus.QUEUED,
        progress=0,
        total_chunks=0,
        embedded_chunks=0,
    )

    db.add(job)

    if commit:
        await db.commit()
        await db.refresh(job)
    else:
        await db.flush()

    return job


# ---------------------------------------------------------------
# GET
# ---------------------------------------------------------------

async def get_job(
    db: AsyncSession,
    job_id: int,
) -> EmbeddingJob | None:

    return await db.get(
        EmbeddingJob,
        job_id,
    )


# ---------------------------------------------------------------
# START
# ---------------------------------------------------------------

async def start_job(
    db: AsyncSession,
    job_id: int,
    total_chunks: int | None = None,
    commit: bool = True,
) -> EmbeddingJob:
    """
    Mark a queued job as PROCESSING.
    """

    job = await get_job(db, job_id)

    if job is None:
        raise ValueError(
            f"Job {job_id} not found"
        )

    if job.status not in (
        JobStatus.QUEUED,
        JobStatus.FAILED,
    ):
        raise ValueError(
            f"Job {job_id} cannot start from "
            f"state {job.status}"
        )

    job.status = JobStatus.PROCESSING
    job.started_at = utc_now()

    job.progress = 0
    job.embedded_chunks = 0
    job.error_message = None
    job.completed_at = None

    if total_chunks is not None:
        if total_chunks < 0:
            raise ValueError(
                "total_chunks cannot be negative"
            )

        job.total_chunks = total_chunks

    if commit:
        await db.commit()
        await db.refresh(job)
    else:
        await db.flush()

    return job


# ---------------------------------------------------------------
# PROGRESS
# ---------------------------------------------------------------

async def update_progress(
    db: AsyncSession,
    job_id: int,
    embedded_chunks: int,
    total_chunks: int | None = None,
    commit: bool = True,
) -> EmbeddingJob:
    """
    Update embedding progress after processing a chunk/batch.
    """

    job = await get_job(db, job_id)

    if job is None:
        raise ValueError(
            f"Job {job_id} not found"
        )

    if job.status != JobStatus.PROCESSING:
        raise ValueError(
            f"Job {job_id} is not PROCESSING "
            f"(current: {job.status})"
        )

    if embedded_chunks < 0:
        raise ValueError(
            "embedded_chunks cannot be negative"
        )

    if total_chunks is not None:
        if total_chunks < 0:
            raise ValueError(
                "total_chunks cannot be negative"
            )

        job.total_chunks = total_chunks

    if (
        job.total_chunks is not None
        and embedded_chunks > job.total_chunks
    ):
        raise ValueError(
            f"embedded_chunks ({embedded_chunks}) "
            f"cannot exceed total_chunks ({job.total_chunks})"
        )

    job.embedded_chunks = embedded_chunks

    if job.total_chunks:
        job.progress = min(
            100,
            int(
                embedded_chunks
                / job.total_chunks
                * 100
            ),
        )
    else:
        job.progress = 0

    if commit:
        await db.commit()
        await db.refresh(job)
    else:
        await db.flush()

    return job


# ---------------------------------------------------------------
# COMPLETE
# ---------------------------------------------------------------

async def complete_job(
    db: AsyncSession,
    job_id: int,
    commit: bool = True,
) -> EmbeddingJob:
    """
    Mark the embedding job as COMPLETED and mark
    the parent document as embedded.
    """

    job = await get_job(db, job_id)

    if job is None:
        raise ValueError(
            f"Job {job_id} not found"
        )

    if job.status != JobStatus.PROCESSING:
        raise ValueError(
            f"Job {job_id} cannot be completed from "
            f"state {job.status}"
        )

    if job.total_chunks:
        job.embedded_chunks = job.total_chunks

    job.progress = 100
    job.status = JobStatus.COMPLETED
    job.completed_at = utc_now()
    job.error_message = None

    # Update parent document
    document = await db.get(
        Document,
        job.document_id,
    )

    if document is None:
        raise ValueError(
            f"Document {job.document_id} not found"
        )

    document.embedded = True

    if commit:
        await db.commit()
        await db.refresh(job)
    else:
        await db.flush()

    return job


# ---------------------------------------------------------------
# FAIL
# ---------------------------------------------------------------

async def fail_job(
    db: AsyncSession,
    job_id: int,
    error: str,
    commit: bool = True,
) -> EmbeddingJob:
    """
    Mark the job as FAILED.
    """

    job = await get_job(db, job_id)

    if job is None:
        raise ValueError(
            f"Job {job_id} not found"
        )

    if job.status == JobStatus.COMPLETED:
        raise ValueError(
            f"Completed job {job_id} cannot be marked as failed"
        )

    job.status = JobStatus.FAILED
    job.error_message = error
    job.completed_at = utc_now()

    if commit:
        await db.commit()
        await db.refresh(job)
    else:
        await db.flush()

    return job


# ---------------------------------------------------------------
# RETRY
# ---------------------------------------------------------------

async def retry_job(
    db: AsyncSession,
    job_id: int,
    commit: bool = True,
) -> EmbeddingJob:
    """
    Move a FAILED job back to QUEUED.
    """

    job = await get_job(db, job_id)

    if job is None:
        raise ValueError(
            f"Job {job_id} not found"
        )

    if job.status != JobStatus.FAILED:
        raise ValueError(
            f"Job {job_id} is not FAILED "
            f"(current: {job.status})"
        )

    job.status = JobStatus.QUEUED

    job.progress = 0
    job.embedded_chunks = 0

    job.error_message = None
    job.started_at = None
    job.completed_at = None

    if commit:
        await db.commit()
        await db.refresh(job)
    else:
        await db.flush()

    return job


# ---------------------------------------------------------------
# LAST JOB FOR DOCUMENT
# ---------------------------------------------------------------

async def get_last_job_for_document(
    db: AsyncSession,
    document_id: int,
) -> EmbeddingJob | None:

    stmt = (
        select(EmbeddingJob)
        .where(
            EmbeddingJob.document_id == document_id
        )
        .order_by(
            desc(EmbeddingJob.created_at),
            desc(EmbeddingJob.id),
        )
        .limit(1)
    )

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


# ---------------------------------------------------------------
# RECENT JOBS
# ---------------------------------------------------------------

async def get_recent_jobs(
    db: AsyncSession,
    limit: int = 20,
) -> list[EmbeddingJob]:

    if limit <= 0:
        raise ValueError(
            "limit must be greater than 0"
        )

    stmt = (
        select(EmbeddingJob)
        .order_by(
            desc(EmbeddingJob.created_at),
            desc(EmbeddingJob.id),
        )
        .limit(limit)
    )

    result = await db.execute(stmt)

    return list(result.scalars().all())


# ---------------------------------------------------------------
# JOBS BY STATUS
# ---------------------------------------------------------------

async def get_jobs_by_status(
    db: AsyncSession,
    status: JobStatus,
    limit: int = 50,
) -> list[EmbeddingJob]:

    if limit <= 0:
        raise ValueError(
            "limit must be greater than 0"
        )

    stmt = (
        select(EmbeddingJob)
        .where(
            EmbeddingJob.status == status
        )
        .order_by(
            desc(EmbeddingJob.created_at),
            desc(EmbeddingJob.id),
        )
        .limit(limit)
    )

    result = await db.execute(stmt)

    return list(result.scalars().all())


# ---------------------------------------------------------------
# DOCUMENT BY JOB
# ---------------------------------------------------------------

async def get_document_by_job(
    db: AsyncSession,
    job_id: int,
) -> Document | None:

    stmt = (
        select(Document)
        .join(
            EmbeddingJob,
            EmbeddingJob.document_id == Document.id,
        )
        .where(
            EmbeddingJob.id == job_id
        )
    )

    result = await db.execute(stmt)

    return result.scalar_one_or_none()