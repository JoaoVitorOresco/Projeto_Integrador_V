from django.urls import path
from .views import PoseEstimationView, VideoUploadView, VideoListView, VideoAnalyticsView, DownloadYouTubeVideoView

urlpatterns = [
    path('estimate/', PoseEstimationView.as_view(), name='estimate_pose'),
    path('videos/upload/', VideoUploadView.as_view(), name='video-upload'),
    path('videos/', VideoListView.as_view(), name='video-list'),
    path('pose/', PoseEstimationView.as_view(), name='pose-estimation'),
    path('videos/<int:video_id>/analytics/', VideoAnalyticsView.as_view(), name='video-analytics'),
    path('videos/download-from-youtube/', DownloadYouTubeVideoView.as_view(), name='download-youtube-video'),
    #path('videos/youtube/<str:youtube_video_id>/delete/', DeleteYouTubeVideoAPIView.as_view(), name='delete-youtube-video'),
]