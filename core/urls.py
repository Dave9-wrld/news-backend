from django.urls import path

from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('auth/password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('sources/', views.SourceListView.as_view(), name='source-list'),
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('articles/mine/', views.MyArticlesView.as_view(), name='my-articles'),
    path('articles/editorial/', views.EditorialQueueView.as_view(), name='editorial-queue'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
    path('articles/<int:pk>/submit/', views.SubmitArticleView.as_view(), name='article-submit'),
    path('articles/<int:pk>/publish/', views.PublishArticleView.as_view(), name='article-publish'),
    path('articles/<int:pk>/return-to-draft/', views.ReturnArticleToDraftView.as_view(), name='article-return-to-draft'),
    path('external-articles/<str:external_id>/', views.ExternalArticleDetailView.as_view(), name='external-article-detail'),
    path('comments/', views.CommentListView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment-detail'),
    path('bookmarks/', views.BookmarkListView.as_view(), name='bookmark-list'),
    path('bookmarks/<int:pk>/', views.BookmarkDetailView.as_view(), name='bookmark-detail'),
]
