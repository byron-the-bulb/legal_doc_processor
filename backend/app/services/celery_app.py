from celery import Celery
from app.core.config import settings
import os

celery_app = Celery(
    "legal_doc_processor",
    broker=settings.BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.services.document_processor"],
)

celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")

# In development, run tasks eagerly so Redis/worker are not required
if settings.ENV == "dev" or os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in {"1", "true", "yes"}:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
