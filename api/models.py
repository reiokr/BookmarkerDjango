from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from .managers import CustomUserManager
# Create your models here.


class CustomUser(AbstractUser):
    username = None
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=250, null=True)
    email = models.EmailField('email address', unique=True)
    is_active = models.BooleanField('is active', default=False)
    categories = ArrayField(models.CharField(
        max_length=20), default=list)
    date_joined = models.DateTimeField(auto_now_add=True, editable=False)
    date_updated = models.DateTimeField(auto_now=True, editable=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'


class UserOptions(models.Model):
    theme = models.IntegerField(default=0)
    localization = models.CharField(max_length=2, default='en')
    settings = models.JSONField()
    owner = models.OneToOneField(
        'CustomUser', related_name='options', on_delete=models.CASCADE)


class Bm(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    bm_type = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    thumbnails = models.JSONField()
    url = models.CharField(max_length=255)
    video_id = models.CharField(max_length=200)
    list_id = models.CharField(
        max_length=200, default="", null=True, blank=True)
    list_index = models.IntegerField(null=True, default=1)
    channel_id = models.CharField(max_length=200)
    channel_title = models.CharField(max_length=100)
    start_at = models.FloatField(blank=True, default=0, null=True)
    keywords = models.JSONField()
    length = models.CharField(max_length=50)
    view_count = models.IntegerField()
    like_count = models.IntegerField()
    comment_count = models.IntegerField()
    privacy_status = models.CharField(max_length=50)
    publish_date = models.DateTimeField(auto_now=False, auto_now_add=False)
    original_category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        'CustomUser', related_name='bookmarks', on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_at']


class Bml(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    bm_type = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=255)
    image_url = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    owner = models.ForeignKey(
        'CustomUser', related_name='bookmark_link', on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_at']
