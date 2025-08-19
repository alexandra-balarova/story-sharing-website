# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.auth.models import User


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def mark_as_read(self):
        self.read = True
        self.save()

    def __str__(self):
        return f"To {self.recipient.username}: {self.message[:20]}..."


class Profile(models.Model):
    name = models.TextField(blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    strike = models.IntegerField(default=0)

    def add_strike(self):
        self.strike += 1
        self.save()

        if self.strike >= 3:
            self.user.is_active = False
            self.user.save()
            Notification.objects.create(recipient=self.user, message="Your account has been deactivated due to 3 strikes.")


    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    liked_by = models.ManyToManyField(Profile, related_name='liked_posts', blank=True)


class Story(Post):
    title = models.CharField(max_length=255)
    public = models.BooleanField(default=False)
    genres = models.ManyToManyField('Genre', blank=True)
    synopsis = models.TextField()
    tags = models.ManyToManyField('Tag', blank=True)
    warnings = models.ManyToManyField('Warning', blank=True)
    fandoms = models.ManyToManyField('Fandom', blank=True)
    bookmarked_by = models.ManyToManyField(Profile, related_name='bookmarked_stories', blank=True)

    def get_absolute_url(self):
        return reverse('story-detail', kwargs={'id': self.id})

    def get_tags_display(self):
        return ', '.join(self.tags.names())

    def get_fandoms_display(self):
        return ', '.join(self.fandoms.names())

    class Meta:
        db_table = "stories"


    def __str__(self):
        return f"{self.title}"

class Chapter(models.Model):
    story = models.ForeignKey(Story, related_name='chapters', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.story.title} chapter {self.title}"

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.name}"


class Warning(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return f"{self.name}"

class Comment(Post):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    def is_reply(self):
        return self.parent is not None

    def __str__(self):
        return f"{self.author}:\n'{self.content}'"

class Fandom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return f"{self.name}"

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return f"{self.name}"


class Reason(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Report(models.Model):
    STATUS_CHOICES = [
        ( "Pending", 'Pending'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reasons = models.ManyToManyField(Reason)
    text = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        deleting_post = False

        if self.pk:
            original = Report.objects.get(pk=self.pk)
            if original.status != 'Resolved' and self.status == 'Resolved':
                deleting_post = True  #flag to delete post after saving

        super().save(*args, **kwargs)

        #post-deletion must occur after the report is saved
        if deleting_post:
            post_author = self.post.author
            self.post.delete()

            if hasattr(post_author, 'profile'):
                post_author.profile.add_strike()

            Notification.objects.create(
                recipient=post_author,
                message="You received a strike due to a resolved report and your post has been deleted."
            )
