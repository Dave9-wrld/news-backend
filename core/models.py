from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        READER = 'reader', 'Reader'
        AUTHOR = 'author', 'Author'
        EDITOR = 'editor', 'Editor'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    # Open contribution model: every new account may create and submit news.
    # Editors still control what becomes publicly published.
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.AUTHOR)

    def __str__(self):
        return f'{self.user.username} ({self.role})'

    @property
    def can_edit(self):
        return self.role == self.Role.EDITOR or self.user.is_staff or self.user.is_superuser


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(max_length=240)
    body = models.TextField(validators=[MinLengthValidator(20)])
    # URL-based covers support CDN-hosted author imagery without requiring a media service.
    cover_image = models.URLField(blank=True)
    cover_image_file = models.FileField(upload_to='article-covers/%Y/%m/', blank=True)
    category = models.CharField(max_length=80, default='general')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='articles')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title


class ExternalArticle(models.Model):
    """Minimal provider metadata used to keep reader interactions stable."""
    external_id = models.CharField(max_length=128, unique=True)
    provider = models.CharField(max_length=32)
    canonical_url = models.URLField(max_length=1000)
    title = models.CharField(max_length=500)
    source_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    category = models.CharField(max_length=80, default='general')
    published_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['-published_at'])]

    def __str__(self):
        return self.title


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    external_article = models.ForeignKey(ExternalArticle, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    body = models.TextField(max_length=2000, validators=[MinLengthValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(article__isnull=False, external_article__isnull=True)
                    | models.Q(article__isnull=True, external_article__isnull=False)
                ),
                name='comment_exactly_one_article_type',
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if bool(self.article_id) == bool(self.external_article_id):
            raise ValidationError('A comment must belong to exactly one article type.')


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='bookmarks', null=True, blank=True)
    external_article = models.ForeignKey(ExternalArticle, on_delete=models.CASCADE, related_name='bookmarks', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(article__isnull=False, external_article__isnull=True)
                    | models.Q(article__isnull=True, external_article__isnull=False)
                ),
                name='bookmark_exactly_one_article_type',
            ),
            models.UniqueConstraint(fields=['user', 'article'], name='unique_original_bookmark'),
            models.UniqueConstraint(fields=['user', 'external_article'], name='unique_external_bookmark'),
        ]
        ordering = ['-created_at']

    def clean(self):
        from django.core.exceptions import ValidationError
        if bool(self.article_id) == bool(self.external_article_id):
            raise ValidationError('A bookmark must belong to exactly one article type.')
