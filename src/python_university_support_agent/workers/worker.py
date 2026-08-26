from arq import run_worker
from .create_embedd_worker import WorkerSettings as CreateEmbeddWorkerSettings


def main():
    run_worker(CreateEmbeddWorkerSettings)


if __name__ == "__main__":
    main()