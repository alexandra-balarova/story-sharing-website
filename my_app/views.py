from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from my_app.models import Story, Chapter, Comment, Post, Notification, Profile
from my_app.forms import StoryForm, ChapterForm, CommentForm, ProfileForm, StorySearchForm, ReportForm
from rest_framework import generics, permissions
from my_app.serializers import NotificationSerializer

def home(request):
    stories = Story.objects.filter(public=True)
    story_list = Story.objects.filter(public=True).order_by('-created_at')
    paginator = Paginator(story_list, 5)  # Show 5 stories per page
    page_number = request.GET.get('page')
    stories = paginator.get_page(page_number)

    return render(request, "index.html", {"stories": stories})

def signup(request):
    form = UserCreationForm(request.POST)
    if form.is_valid():
        form.save()  # save the user
        return redirect('/')
    else:
        form = UserCreationForm()
        return render(request, 'register.html', {'form': form})

def story_detail(request, pk):
    story = get_object_or_404(Story, id=pk)
    chapter_id = request.GET.get('chapter')
    chapter = None
    next_chapter = None

    if chapter_id:
        chapter = get_object_or_404(Chapter, pk=chapter_id)
        # Get the next chapter by ordering (e.g., by pk or a chapter number)
        next_chapter = story.chapters.filter(pk__gt=chapter.pk).order_by('pk').first()
    else:
        chapter = story.chapters.order_by('pk').first()
        if chapter:
            next_chapter = story.chapters.filter(pk__gt=chapter.pk).order_by('pk').first()

    form = CommentForm()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = story
            comment.parent = None


            comment.save()
            Notification.objects.create(recipient=story.author,
                                        message=f"{request.user} just commented your story {story.title}!")
            return redirect('story-detail', pk=story.pk)

    context = {
        'story': story,
        'tags': story.tags.all(),
        'genres': story.genres.all(),
        'fandoms': story.fandoms.all(),
        'warnings': story.warnings.all(),
        'chapter': chapter,
        'next_chapter': next_chapter,
        'comments': story.comments.all().filter(parent=None),
        'is_own_story': (story.author == request.user),
        'form' : form,
    }
    return render(request, "post.html", context)

def comment_view(request, pk):
    story = get_object_or_404(Story, id=pk)

    form = CommentForm()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = story
            comment.parent = None
            comment.save()
            Notification.objects.create(recipient=story.author,
                                        message=f"{request.user} just commented your story {story.title}!")
            return redirect(request.META.get('HTTP_REFERER', '/'))

    context = {
        'story': story,
        'tags': story.tags.all(),
        'genres': story.genres.all(),
        'fandoms': story.fandoms.all(),
        'warnings': story.warnings.all(),
        'comments': story.comments.all().filter(parent=None),
        'is_own_story': (story.author == request.user),
        'form': form,
    }
    return render(request, "post_comments.html", context)


def toggle_replies(request, story_pk, comment_pk):
    story = get_object_or_404(Story, pk=story_pk)
    parent_comment = get_object_or_404(Comment, pk=comment_pk)
    next_page = request.GET.get('next', 'story-detail')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.author = request.user
            reply.parent = parent_comment
            reply.post = story
            reply.save()
            if request.user is not story.author:
                Notification.objects.create(recipient=story.author,
                                            message=f"{request.user} just commented on your story {story.title}!")

            if request.user is not reply.parent.author:
                Notification.objects.create(recipient=reply.parent.author,
                                            message=f"{request.user} just replied to your comment '{reply.parent.content}'!")

            return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = CommentForm()

    context = {
        'comment': parent_comment,
        'form': form,
    }
    if next_page == 'story-detail':
        return render(request, "post.html", context)
    else:
        return render(request, "post_comments.html", context)

def edit_profile(request):
    user = request.user
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profile_edit.html', {'form': form})

def profile_view(request, username = None):
    try:
        user = get_object_or_404(User, username=username) if username else request.user
    except User.DoesNotExist:
        user = request.user

    context = {
        'profile_user': user,
        'profile': user.profile,
        'stories': Story.objects.filter(author=user),
        'bookmarks': user.profile.bookmarked_stories.all(),
        'is_own_profile': (user == request.user)
    }
    return render(request, 'profile.html', context)


class story_create(LoginRequiredMixin, CreateView):
    model = Story
    form_class = StoryForm
    template_name = 'story_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('story-detail', kwargs={'pk': self.object.pk})


class story_edit(LoginRequiredMixin, UpdateView):
    model = Story
    form_class = StoryForm
    template_name = 'story_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['story'] = self.object
        return context

    def get_queryset(self):
        return Story.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('story-detail', kwargs={'pk': self.object.pk})

class add_chapter(LoginRequiredMixin, CreateView):
    model = Chapter
    form_class = ChapterForm
    template_name = 'chapter_form.html'


    def form_valid(self, form):
        story = get_object_or_404(Story, pk=self.kwargs['story_pk'])
        form.instance.story = story
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('story-detail', kwargs={'pk': self.kwargs['story_pk']})

def publish_chapter(request, story_pk, chapter_pk):
    chapter = get_object_or_404(Chapter, pk=chapter_pk)
    story = get_object_or_404(Story, pk = story_pk)

    if story.public:
        chapter.public = True
        chapter.save()
        for user in story.bookmarked_by.all():
            Notification.objects.create(recipient=user.user, message=f"{story.author} just posted a new chapter to {story.title}!")

    return redirect(request.META.get('HTTP_REFERER', '/'))

def private_chapter(request, story_pk, chapter_pk):
    chapter = get_object_or_404(Chapter, pk=chapter_pk)

    chapter.public = False
    chapter.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))


def test_view(request):
    ch = Chapter.objects.first()
    ch.public = not ch.public
    ch.save()
    return HttpResponse(f"Toggled to {ch.public}")

class edit_chapter(LoginRequiredMixin, UpdateView):
    model = Chapter
    form_class = ChapterForm
    template_name = 'chapter_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['story'] = self.story
        return context

    def get_queryset(self):
        self.story = get_object_or_404(Story, pk=self.kwargs['story_pk'])
        return Chapter.objects.filter(story = self.story)

    def get_success_url(self):
        return reverse_lazy('story-detail', kwargs={'pk': self.kwargs['story_pk']})


@login_required
def follow(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    print("user:",profile)
    follower = request.user.profile
    print("follower:",follower)

    if follower in profile.followers.all():
        profile.followers.remove(follower)
        print(f"{follower.user} unfollowed {profile.user}")
    else:
        profile.followers.add(follower)
        print(f"{follower.user} followed {profile.user}")

        Notification.objects.create(recipient=profile.user, message=f"{follower.user} just followed you!")

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def likes(request, pk, story_pk = None):
    post = get_object_or_404(Post, pk=pk)
    if request.user.profile in post.liked_by.all():
        post.liked_by.remove(request.user.profile)
    else:
        post.liked_by.add(request.user.profile)
        if story_pk:
            comment = get_object_or_404(Comment, pk=pk)
            Notification.objects.create(recipient=post.author, message=f"{request.user} just liked your comment {comment.content}!")

        else:
            story = get_object_or_404(Story, pk=pk)
            Notification.objects.create(recipient=story.author,
                                        message=f"{request.user} just liked your story {story.title}!")

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def bookmarks(request, pk):
    story = get_object_or_404(Story, pk=pk)
    if request.user.profile in story.bookmarked_by.all():
        story.bookmarked_by.remove(request.user.profile)
    else:
        story.bookmarked_by.add(request.user.profile)
        Notification.objects.create(recipient=story.author, message=f"{request.user} just bookmarked your story {story.title}!")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def delete(request, pk, story_pk = None):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def delete_chapter(request, story_pk, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    chapter.delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def report(request, pk, story_pk = None):
    post = get_object_or_404(Post, pk=pk)

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.post = post
            report.reporter = request.user
            report.save()
            form.save_m2m()


            redirect_url = request.META.get('HTTP_REFERER', None)
            if not redirect_url or 'report' in redirect_url:
                redirect_url = reverse('home-page')
            return redirect(redirect_url)
    else:
        form = ReportForm()

    return render(request, 'report_post.html', {'form': form, 'post': post})

def story_search(request):
    form = StorySearchForm(request.GET or None)
    stories = Story.objects.all()

    if form.is_valid():
        q = form.cleaned_data.get('query', '').strip()
        exclude_warnings = form.cleaned_data.get('warnings')
        exclude_genres = form.cleaned_data.get('genres')

        if q:
            # Search title, author username, tags, fandoms
            stories = stories.filter(
                Q(title__icontains=q) |
                Q(author__username__icontains=q) |
                Q(tags__name__icontains=q) |
                Q(fandoms__name__icontains=q)
            ).distinct()

        if exclude_warnings:
            stories = stories.exclude(warnings__in=exclude_warnings)

        if exclude_genres:
            stories = stories.exclude(genres__in=exclude_genres)

    context = {
        'form': form,
        'stories': stories,
    }
    return render(request, 'search_form.html', context)

class notification_list_api(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


class notification_mark_read_api(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user, read=False)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.read = True
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


