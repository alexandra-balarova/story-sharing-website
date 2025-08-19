"""
URL configuration for djangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from my_app import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name = "home-page" ),
    path('register/', views.signup, name="reg-page"),
    path('login/', LoginView.as_view(template_name="login.html"), name="login"),
    path('logout/', LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name="logout"),
    path('story/new/', views.story_create.as_view(), name="create-story"),
    path('story/<int:pk>/edit/', views.story_edit.as_view(), name="edit-story"),
    path('story/<int:pk>/like/', views.likes, name="likes"),
    path('story/<int:pk>/bookmark/', views.bookmarks, name="bookmarks"),
    path('story/<int:pk>/comments/', views.comment_view, name="comment-page"),
    path('story/<int:story_pk>/comment/<int:pk>/like/', views.likes, name="likes-comments"),
    path('story/<int:pk>/delete/', views.delete, name="delete"),
    path('story/<int:story_pk>/comment/<int:pk>/delete/', views.delete, name="delete-comments"),
    path('story/<int:story_pk>/comments/<int:comment_pk>/reply/', views.toggle_replies, name="reply"),
    path('story/<int:story_pk>/chapter/new', views.add_chapter.as_view(), name='chapter-add'),
    path('story/<int:story_pk>/chapter/<int:pk>/edit', views.edit_chapter.as_view(), name="chapter-edit"),
    path('story/<int:story_pk>/chapter/<int:chapter_pk>/publish', views.publish_chapter, name="publish-chapter"),
    path('story/<int:story_pk>/chapter/<int:chapter_pk>/private', views.private_chapter,  name="private-chapter"),
    path('story/<int:story_pk>/chapter/<int:pk>/delete/', views.delete_chapter, name="delete-chapter"),
    path('story/<int:pk>/report/', views.report, name="report"),
    path('story/<int:story_pk>/comment/<int:pk>/report/', views.report, name="report-comments"),
    path('story/<int:pk>/detail/', views.story_detail, name="story-detail"),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit', views.edit_profile, name="edit-profile" ),
    path('profile/<str:username>/', views.profile_view, name='user-profile'),
    path('profile/follow/<str:username>/', views.follow, name='follow'),
    path('search/', views.story_search, name = 'story-search'),
    path('api/notifications/', views.notification_list_api.as_view(), name='notification-list'),
    path('api/notifications/mark-read/<int:pk>/', views.notification_mark_read_api.as_view(), name='notification-read'),
    path('test-toggle/', views.test_view, name='test-toggle'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


