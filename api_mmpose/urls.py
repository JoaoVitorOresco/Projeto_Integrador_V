from django.urls import path
from .views import PoseEstimationView, VideoUploadView, VideoListView, VideoAnalyticsView

urlpatterns = [
    path('estimate/', PoseEstimationView.as_view(), name='estimate_pose'),
    path('videos/upload/', VideoUploadView.as_view(), name='video-upload'),
    path('videos/', VideoListView.as_view(), name='video-list'),
    path('pose/', PoseEstimationView.as_view(), name='pose-estimation'),
    path('videos/<int:video_id>/analytics/', VideoAnalyticsView.as_view(), name='video-analytics'),
]