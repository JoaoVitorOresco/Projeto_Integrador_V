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
            'processing_status', 'processing_log',
            'youtube_video_id',         
            'youtube_upload_status',    
            'original_file_cleaned_up', 
            'processed_file_cleaned_up'
        ]
        read_only_fields = [
            'user', 'username', 'uploaded_at', 'video_url', 
            'processed_video_url', 'processing_status', 'processing_log',
            'youtube_video_id', 'youtube_upload_status',
            'original_file_cleaned_up', 'processed_file_cleaned_up'
        ]

    def get_video_url(self, obj):
        request = self.context.get('request')
        if request and obj.video_file and hasattr(obj.video_file, 'url'):
            return request.build_absolute_uri(obj.video_file.url)
        return None
    
    def get_processed_video_url(self, obj):
        request = self.context.get('request')
        if request and obj.processed_video_file and hasattr(obj.processed_video_file, 'url'):
            return request.build_absolute_uri(obj.processed_video_file.url)
        return None


class VideoUploadSerializer(serializers.Serializer):
    video = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    description = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_video(self, value):
        # Limite de tamanho de 1GB para vídeos (ajuste conforme necessário)
        # O YouTube tem limites maiores, mas isso é para o upload inicial para o seu servidor.
        MAX_SIZE_MB = 1024 
        if value.size > MAX_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(f"O arquivo de vídeo não pode exceder {MAX_SIZE_MB}MB.")
        
        # Validação de tipo de conteúdo mais flexível, mas ainda focada em vídeo
        allowed_video_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm']
        if value.content_type not in allowed_video_types:
            print(f"AVISO (UploadSerializer): Tipo de conteúdo não permitido - {value.content_type}")
            # Considere se quer ser mais restritivo ou mais permissivo
            # raise serializers.ValidationError(f"Formato de vídeo inválido. Tipos permitidos: {', '.join(allowed_video_types)}.")
        return value

    def create(self, validated_data):
        # Este serializer é para validação de entrada, não para criar objetos diretamente.
        # A criação do objeto Video é feita na view.
        return validated_data
