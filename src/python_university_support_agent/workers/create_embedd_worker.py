from arq.connections import RedisSettings
from ..config import settings
from ..jobs import create_embedd

class WorkerSettings:
    functions = [
        create_embedd
    ]
    queue_name     = "embedd_docs_queue"
    redis_settings = RedisSettings( host= settings.redis_host, port = int(settings.redis_port))
    max_jobs = 50          # high concurrency, low latency
    job_timeout = 1800

