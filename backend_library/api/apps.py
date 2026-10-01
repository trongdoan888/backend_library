from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        post_save.connect(_on_save, dispatch_uid="audit_post_save")
        post_delete.connect(_on_delete, dispatch_uid="audit_post_delete")


def _on_save(sender, instance, created, **kwargs):
    if sender._meta.app_label != "api":
        return
    from api.audit import log_event
    # Chỉ log model/pk, không log giá trị field - User.password là hash nhưng
    # vẫn không có lý do gì để field value xuất hiện trong log CRUD.
    log_event("database", "create" if created else "update", "success",
              resource=sender.__name__, resource_id=str(instance.pk))


def _on_delete(sender, instance, **kwargs):
    if sender._meta.app_label != "api":
        return
    from api.audit import log_event
    log_event("database", "delete", "success", resource=sender.__name__, resource_id=str(instance.pk))
