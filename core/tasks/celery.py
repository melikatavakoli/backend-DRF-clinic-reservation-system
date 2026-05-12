from celery import shared_task


@shared_task
def test_beat():
    print("Celery Beat is working!")
    return "Task executed!"