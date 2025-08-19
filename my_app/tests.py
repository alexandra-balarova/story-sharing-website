from django.test import TestCase
from my_app.models import Profile, Story, Genre, Warning, Fandom, Comment, Report, Reason, Post
from my_app.forms import ProfileForm, StoryForm, CommentForm, ReportForm, ChapterForm
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from my_app.models import Notification


class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')

    def test_profile_created_on_user_creation(self):
        # Profile should be auto-created on user creation
        profile = Profile.objects.get(user=self.user)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user.username, 'testuser')

    def test_add_strike_and_deactivate(self):
        profile = self.user.profile
        self.assertEqual(profile.strike, 0)
        self.assertTrue(self.user.is_active)

        # Add 3 strikes
        for _ in range(3):
            profile.add_strike()

        profile.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(profile.strike, 3)
        self.assertFalse(self.user.is_active)
        self.assertTrue(profile.user.notifications.filter(message__icontains='deactivated').exists())


class StoryFormTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='Fantasy')
        self.warning = Warning.objects.create(name='Violence')

    def test_story_form_valid_and_save(self):

        form_data = {
            'title': 'My Story',
            'synopsis': 'Synopsis here',
            'public': True,
            'tags': '#fantasy #adventure',
            'fandoms': 'Fandom1, Fandom2',
            'genres': [self.genre.pk],
            'warnings': [self.warning.pk],
        }
        author = User.objects.create_user(username='author', password='pass')
        form = StoryForm(data=form_data)
        self.assertTrue(form.is_valid())

        story = form.save(commit=True, author=author)  # Save instance + all M2M including fandoms

        story.save()
        form.save_m2m()

        self.assertEqual(story.title, 'My Story')
        self.assertTrue(story.tags.filter(name='fantasy').exists())
        self.assertTrue(story.tags.filter(name='adventure').exists())
        self.assertTrue(story.fandoms.filter(name='Fandom1').exists())
        self.assertTrue(story.fandoms.filter(name='Fandom2').exists())
        self.assertTrue(story.genres.filter(name='Fantasy').exists())
        self.assertTrue(story.warnings.filter(name='Violence').exists())


class CommentFormTest(TestCase):
    def test_comment_form_valid(self):
        form_data = {'content': 'Nice story!'}
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
        comment = form.save(commit=False)
        self.assertEqual(comment.content, 'Nice story!')

class ChapterFormTest(TestCase):
    def test_chapter_form_valid_and_save(self):

        form_data = {
            'title': 'My Chapter',
            'content': 'Chapter Content Here.'
        }
        form = ChapterForm(data=form_data)
        self.assertTrue(form.is_valid())


        chapter = form.save(commit=False)


        self.assertEqual(chapter.title, 'My Chapter')
        self.assertEqual(chapter.content,  'Chapter Content Here.')
        self.assertFalse(chapter.public)


class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reporter', password='pass')
        self.author = User.objects.create_user(username='author', password='pass')
        self.reason = Reason.objects.create(name='Spam')
        self.story = Story.objects.create(author=self.author, title='Story', synopsis='...', public=True)

    def test_report_strike_and_notification_on_resolved(self):
        report = Report.objects.create(post=self.story, reporter=self.user)
        report.reasons.add(self.reason)
        report.status = 'Pending'
        report.save()

        self.assertEqual(report.status, 'Pending')

        # Change status to resolved triggers strike and notification
        report.status = 'Resolved'
        report.save()

        self.author.refresh_from_db()
        self.assertEqual(self.author.profile.strike, 1)
        self.assertTrue(self.author.notifications.filter(message__icontains='strike').exists())

class ReportFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test reasons
        cls.reason1 = Reason.objects.create(name="Spam")
        cls.reason2 = Reason.objects.create(name="Inappropriate Content")
        cls.reason3 = Reason.objects.create(name="Harassment")


    def test_report_valid_and_save_form(self):
        form_data = {
            'reasons':  [self.reason1.id],
            'text': 'Optional Text.'
        }
        user = User.objects.create_user(username='reporter', password='pass')
        author = User.objects.create_user(username='author', password='pass')
        post = Post.objects.create(author=author)

        form = ReportForm(data=form_data)

        report = form.save(commit=False)
        report.reporter = user
        report.post = post
        report.save()
        form.save_m2m()

        self.assertEqual(report.text, 'Optional Text.')
        self.assertEqual(report.reasons.count(), 1)
        self.assertIn(self.reason1, report.reasons.all())

        report.status = 'Resolved'
        report.save()
        self.assertFalse(Post.objects.filter(pk=report.post.pk).exists())


class SignupViewTests(TestCase):
    def test_signup_page_renders(self):
        response = self.client.get(reverse('reg-page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_signup_creates_user_and_redirects(self):
        response = self.client.post(reverse('reg-page'), {
            'username': 'newuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertRedirects(response, '/')
        self.assertTrue(User.objects.filter(username='newuser').exists())


class StoryCreateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.url = reverse('create-story')

    def test_create_story_success(self):
        self.client.login(username='testuser', password='pass')
        response = self.client.post(self.url, {
            'title': 'Test Story',
            'synopsis': 'Synopsis here',
            'public': True,
            'tags': '#fantasy #test',
            'genres': [],
            'warnings': [],
        })
        story = Story.objects.first()
        self.assertIsNotNone(story)
        self.assertEqual(story.title, 'Test Story')
        self.assertEqual(story.author, self.user)
        self.assertRedirects(response, reverse('story-detail', kwargs={'pk': story.pk}))

class StoryDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commenter', password='pass')
        self.author = User.objects.create_user(username='author', password='pass')
        self.story = Story.objects.create(title='Test Story', author=self.author, public=True)
        self.url = reverse('story-detail', kwargs={'pk': self.story.pk})

    def test_view_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)

    def test_post_comment_logged_in(self):
        self.client.login(username='commenter', password='pass')
        response = self.client.post(self.url, {'content': 'Nice story!'})
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.author, self.user)
        self.assertRedirects(response, self.url)


class LikesToggleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='liker', password='pass')
        self.story = Story.objects.create(title='Liked Story', author=self.user)
        self.url = reverse('likes', kwargs={'pk': self.story.pk})



    def test_toggle_like_adds_and_removes(self):
        self.client.login(username='liker', password='pass')
        response = self.client.post(self.url)
        self.assertIn(self.user.profile, self.story.liked_by.all())

        response = self.client.post(self.url)
        self.assertNotIn(self.user.profile, self.story.liked_by.all())


class BookmarksToggleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bookmarker', password='pass')
        self.story = Story.objects.create(title='Bookmarked Story', author=self.user)
        self.url = reverse('bookmarks', kwargs={'pk': self.story.pk})



    def test_toggle_bookmark_adds_and_removes(self):
        self.client.login(username='bookmarker', password='pass')
        response = self.client.post(self.url)
        self.assertIn(self.user.profile, self.story.bookmarked_by.all())

        response = self.client.post(self.url)
        self.assertNotIn(self.user.profile, self.story.bookmarked_by.all())

class StorySearchTests(TestCase):
    def setUp(self):
        author = User.objects.create_user(username='author', password='pass')
        self.story1 = Story.objects.create(author = author, title='Adventure Story', public=True)
        self.story2 = Story.objects.create(author = author, title='Romance Story', public=True)

    def test_search_returns_matching_stories(self):
        response = self.client.get(reverse('story-search'), {'query': 'Adventure'})
        self.assertContains(response, self.story1.title)
        self.assertNotContains(response, self.story2.title)


#API tests

class NotificationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass')
        self.client = APIClient()

        # Create notifications
        self.n1 = Notification.objects.create(recipient=self.user, message='Test Notification 1')
        self.n2 = Notification.objects.create(recipient=self.user, message='Test Notification 2', read=True)
        self.n3 = Notification.objects.create(recipient=self.other_user, message='Not Yours')

        self.list_url = reverse('notification-list')
        self.mark_read_url = reverse('notification-read',
                                     kwargs={'pk': self.n1.pk})

    def test_notification_list_requires_authentication(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 403)  # or 401 depending on your settings

    def test_list_notifications(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        for note in response.data:
            self.assertIn(note['message'], ['Test Notification 1', 'Test Notification 2'])

    def test_mark_notification_as_read(self):
        self.client.login(username='testuser', password='testpass')

        url = reverse('notification-read', kwargs={'pk': self.n1.pk})
        response = self.client.patch(url)

        self.assertEqual(response.status_code, 200)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.read)

    def test_cannot_mark_other_users_notification(self):
        self.client.login(username='testuser', password='testpass')

        url = reverse('notification-read', kwargs={'pk': self.n3.pk})
        response = self.client.patch(url)

        self.assertEqual(response.status_code, 404)
