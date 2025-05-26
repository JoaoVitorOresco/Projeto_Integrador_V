from django.db import models
from django.conf import settings
import os

class Video(models.Model):
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=255, blank=True, null=True)
    video_file = models.FileField(upload_to='videos/originals/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    youtube_video_id = models.CharField(max_length=50, blank=True, null=True)
    youtube_upload_status = models.CharField(max_length=50, blank=True, null=True)
    original_file_cleaned_up = models.BooleanField(default=False)
    processed_file_cleaned_up = models.BooleanField(default=False)
    processed_video_file = models.FileField(upload_to='videos/processed/', blank=True, null=True)
    processing_status = models.CharField(
        max_length=50,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending'
    )
    processing_log = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title or f"Video by {self.user.username} uploaded on {self.uploaded_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-uploaded_at']

    @property
    def original_filename(self):
        if self.video_file:
            return os.path.basename(self.video_file.name)
        return None

    @property
    def processed_filename(self):
        if self.processed_video_file:
            return os.path.basename(self.processed_video_file.name)
        return None

class FrameData(models.Model):
    video = models.ForeignKey(Video, related_name='frame_data', on_delete=models.CASCADE)
    frame_number = models.IntegerField(db_index=True) 
    player_label = models.IntegerField() 


    combat_state = models.CharField(max_length=50, blank=True, null=True)


    # Ombro Esquerdo (índice 0 na fatia)
    shoulder_left_x = models.FloatField(null=True, blank=True)
    shoulder_left_y = models.FloatField(null=True, blank=True)
    # Ombro Direito (índice 1 na fatia)
    shoulder_right_x = models.FloatField(null=True, blank=True)
    shoulder_right_y = models.FloatField(null=True, blank=True)
    # Cotovelo Esquerdo (índice 2 na fatia)
    elbow_left_x = models.FloatField(null=True, blank=True)
    elbow_left_y = models.FloatField(null=True, blank=True)
    # Cotovelo Direito (índice 3 na fatia)
    elbow_right_x = models.FloatField(null=True, blank=True)
    elbow_right_y = models.FloatField(null=True, blank=True)
    # Pulso Esquerdo (índice 4 na fatia)
    wrist_left_x = models.FloatField(null=True, blank=True)
    wrist_left_y = models.FloatField(null=True, blank=True)
    # Pulso Direito (índice 5 na fatia)
    wrist_right_x = models.FloatField(null=True, blank=True)
    wrist_right_y = models.FloatField(null=True, blank=True)
    # Quadril Esquerdo (índice 6 na fatia)
    hip_left_x = models.FloatField(null=True, blank=True)
    hip_left_y = models.FloatField(null=True, blank=True)
    # Quadril Direito (índice 7 na fatia)
    hip_right_x = models.FloatField(null=True, blank=True)
    hip_right_y = models.FloatField(null=True, blank=True)
    # Joelho Esquerdo (índice 8 na fatia)
    knee_left_x = models.FloatField(null=True, blank=True)
    knee_left_y = models.FloatField(null=True, blank=True)
    # Joelho Direito (índice 9 na fatia)
    knee_right_x = models.FloatField(null=True, blank=True)
    knee_right_y = models.FloatField(null=True, blank=True)
    # Tornozelo Esquerdo (índice 10 na fatia)
    ankle_left_x = models.FloatField(null=True, blank=True)
    ankle_left_y = models.FloatField(null=True, blank=True)
    # Tornozelo Direito (índice 11 na fatia)
    ankle_right_x = models.FloatField(null=True, blank=True)
    ankle_right_y = models.FloatField(null=True, blank=True)

    left_leg_angle = models.FloatField(null=True, blank=True)
    right_leg_angle = models.FloatField(null=True, blank=True)
    front_leg = models.IntegerField(null=True, blank=True) 
    front_wrist = models.IntegerField(null=True, blank=True) 
    arm_base_distance = models.FloatField(null=True, blank=True)
    cup_above = models.IntegerField(null=True, blank=True)

    class Meta:
        # Garante que cada jogador só tem um registo por frame de um vídeo específico
        unique_together = ('video', 'frame_number', 'player_label')
        ordering = ['video', 'frame_number', 'player_label']

    def __str__(self):
        return f"Video {self.video.id} - Frame {self.frame_number} - Player {self.player_label}"
