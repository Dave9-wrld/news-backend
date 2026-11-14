from django.contrib import admin
from django.utils import timezone

from .models import Article, Bookmark, Comment, ExternalArticle, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'updated_at', 'published_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'body', 'author__username')
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'published_at')
    list_select_related = ('author',)
    actions = ('publish_submitted', 'return_to_draft')

    @admin.action(description='Publish selected submitted articles')
    def publish_submitted(self, request, queryset):
        now = timezone.now()
        updated = queryset.filter(status=Article.Status.SUBMITTED).update(
            status=Article.Status.PUBLISHED,
            published_at=now,
            updated_at=now,
        )
        self.message_user(request, f'{updated} submitted article(s) published.')

    @admin.action(description='Return selected articles to draft')
    def return_to_draft(self, request, queryset):
        now = timezone.now()
        updated = queryset.exclude(status=Article.Status.PUBLISHED).update(
            status=Article.Status.DRAFT,
            submitted_at=None,
            updated_at=now,
        )
        self.message_user(request, f'{updated} article(s) returned to draft.')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'external_article', 'created_at')
    search_fields = ('body', 'user__username')
    list_select_related = ('user', 'article', 'external_article')


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'external_article', 'created_at')
    list_select_related = ('user', 'article', 'external_article')


@admin.register(ExternalArticle)
class ExternalArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'source_name', 'published_at', 'last_seen_at')
    search_fields = ('title', 'canonical_url', 'source_name')
    readonly_fields = ('last_seen_at',)
