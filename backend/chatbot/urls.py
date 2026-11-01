from django.urls import path
from .views import chat, health, upload_document, list_documents, delete_document

urlpatterns = [
    path("health/", health, name="health"),
    path("chat/", chat, name="chat"),
    path("documents/upload/", upload_document, name="upload_document"),
    path("documents/", list_documents, name="list_documents"),
    path("documents/<str:document_id>/", delete_document, name="delete_document"),
]
