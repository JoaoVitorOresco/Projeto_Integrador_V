from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    video_url = serializers.SerializerMethodField()
    processed_video_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'user', 'username', 'title', 
            'video_file', 'video_url', 
            'processed_video_file', 'processed_video_url',
            'uploaded_at', 'description',
            'processing_status', 'processing_log' 
        ]
        read_only_fields = [
            'user', 'username', 'uploaded_at', 'video_url', 
            'processed_video_url', 'processing_status', 'processing_log'
        ]

    def get_video_url(self, obj):
        request = self.context.get('request')
        if request and obj.video_file:
            return request.build_absolute_uri(obj.video_file.url)
        return None
    
    def get_processed_video_url(self, obj):
        request = self.context.get('request')
        if request and obj.processed_video_file:
            return request.build_absolute_uri(obj.processed_video_file.url)
        return None


class VideoUploadSerializer(serializers.Serializer):
    video = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_video(self, value):
        if value.size > 100 * 1024 * 1024:
            raise serializers.ValidationError("O arquivo de vídeo não pode exceder 100MB.")
        if not value.content_type in ['video/mp4', 'video/quicktime']:
            raise serializers.ValidationError("Formato de vídeo inválido. Apenas MP4 ou MOV são permitidos.")
        return value