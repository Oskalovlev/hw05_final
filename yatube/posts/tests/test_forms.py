from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
import tempfile

from posts.models import Post, Group, Comment

User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
            description='Описание',
        )
        cache.clear()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create_post(self):
        """Проверка создания поста"""
        before_creating_post = set(Post.objects.values_list('id', flat=True))
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст нового поста',
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        after_creating_post = set(Post.objects.values_list('id', flat=True))
        post_difference = after_creating_post.difference(before_creating_post)
        self.assertEqual(len(post_difference), 1)
        post_id = post_difference.pop()
        post = Post.objects.get(id=post_id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(uploaded, form_data['image'])

    def test_edit_post(self):
        """Проверка редактирования поста"""
        form_data = {
            'text': 'Текст редактирования',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data['group'])


class TestComments(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
        )

    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comments_authorized_user(self):
        """Комментировать может только авторизованный пользователь"""
        comment_count_before = Comment.objects.count() + 1
        form_data = {
            'text': 'Текст нового поста',
        }
        autorized = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        guest = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        coment = Comment.objects.get(text=form_data['text'])
        comment_count_after = Comment.objects.count()
        if autorized:
            self.assertEqual(comment_count_before, comment_count_after)
            self.assertEqual(coment.text, form_data['text'])
        if guest:
            self.assertNotEqual(comment_count_before, comment_count_after + 1)
