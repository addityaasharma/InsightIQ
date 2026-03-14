from utils.celery.celery_app import celery
from services.analysis_service import analyze_dataset


@celery.task(name="dataset.analysis", bind=True, max_retries=3)
def run_dataset_analysis(self, dataset_id):
    try:
        from model import Dataset  # ← import inside task, not at top level

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return {"status": "error", "message": "Dataset not found"}

        analyze_dataset(dataset, dataset.file_path)
        return {"status": "success", "message": "Dataset analysis completed"}
    except Exception as e:
        print(f"Task error: {e}")
        raise self.retry(exc=e, countdown=5)
