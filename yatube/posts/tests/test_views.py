from math import ceil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post

User = get_user_model()


class PostsViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
            description='Описание',
        )
        cls.anothe_group = Group.objects.create(
            title='Заголовок другой группы',
            slug='anothe-slug',
            description='Описание другой группы',
        )
        cls.user = User.objects.create_user(username='auth')
        cls.user_anothe = User.objects.create_user(username='auth-anothe')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
        )

    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_profile_and_group_list_page_show_correct_context(self):
        """Шаблоны profile и group_list сформированы с правильным контекстом"""
        response_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'slug'})
        )
        pages_check_context: list = [
            (response_profile.context['author'], self.user),
            (response_group_list.context['group'], self.post.group)
        ]
        for page_context, check in pages_check_context:
            self.assertEqual(page_context, check)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post: list = [
            (response.context['post'].text, self.post.text),
            (response.context['post'].group, self.post.group),
            (response.context['post'].author, self.post.author),
        ]
        for value, expected in post:
            self.assertEqual(value, expected)

    def test_post_create_and_post_edit_page_show_correct_form(self):
        """Шаблон post_create и post_edit сформирован с правильной формой"""
        pages: tuple = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id, })
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertIsInstance(
                    response.context['form'], PostForm
                )

    def test_post_edit_page_show_correct_post(self):
        """Для страницы post_edit в форму передан нужный пост """
        page = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        response = self.authorized_client.get(page)
        self.assertEqual(
            response.context['form'].instance, self.post
        )

    def test_post_add_correct(self):
        """Пост добавлен корректно"""
        pages: tuple = (
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
            # reverse('posts:follow_index'),
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                context_page = response.context['page_obj']
                self.assertIn(self.post, context_page, 'поста нет')

    def test_post_not_in_another_group(self):
        """Пост не отобраежается в другой группе"""
        page = reverse(
            'posts:group_list', kwargs={'slug': self.anothe_group.slug}
        )
        response = self.authorized_client.get(page)
        context_page = response.context['page_obj']
        self.assertNotIn(self.post, context_page, 'пост есть')

    def test_cache_index(self):
        """Проверка кэша для индекса"""
        response = self.authorized_client.get(reverse('posts:index'))
        before_posts = response.content
        Post.objects.create(
            text='Проверка кэша',
            author=self.post.author,
        )
        response_another = self.authorized_client.get(reverse('posts:index'))
        another_post = response_another.content
        self.assertEqual(another_post, before_posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        next_post = response_new.content
        self.assertNotEqual(another_post, next_post)

    def test_follow(self):
        """Проверка подписки на автора пользователем"""
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.user_anothe.username]),
            follow=True
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user_anothe
            ).exists()
        )

    def test_unfollow(self):
        """Проверка отписки позьзователя"""
        Follow.objects.create(
            user=self.user,
            author=self.user_anothe
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                args=[self.user_anothe.username]
            ),
            follow=True
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user_anothe
            ).exists()
        )

    def test_appears_feed_subscribed(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан
        """
        self.authorized_client.force_login(self.user_anothe)
        Follow.objects.create(
            user=self.user_anothe,
            author=self.user
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        post = response.context['page_obj']
        self.assertIn(self.post, post)

    def test_appears_no_feed_unsubscribed(self):
        """
        Новая запись не появляется в ленте тех,
        кто не подписан
        """
        Follow.objects.create(
            user=self.user_anothe,
            author=self.user
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        post = response.context['page_obj']
        self.assertNotIn(self.post, post)


class TestPaginatorViews(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEST_NUMBER_OF_POST: int = 7
        cls.user = User.objects.create(
            username='auth',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        Post.objects.bulk_create([
            Post(
                text=f'Тестовый пост {post_num}',
                author=cls.user,
                group=cls.group,
            )
            for post_num in range(cls.TEST_NUMBER_OF_POST)
        ])
        cls.page_count = ceil(
            cls.TEST_NUMBER_OF_POST / settings.NUMBER_OF_POSTS
        )
        cls.page_size = (cls.TEST_NUMBER_OF_POST
                         - (cls.page_count - 1)
                         * settings.NUMBER_OF_POSTS)

    def setUp(self):
        self.client = Client()

    def test_paginator_on_pages(self):
        """Проверка paginator на страницах"""
        pages: list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for page in pages:
            with self.subTest(page_=page):
                response_first_page = len(
                    self.client.get(page).context['page_obj']
                )
                self.assertEqual(
                    response_first_page,
                    self.page_size
                )
                response_next_page = len(
                    self.client.get(
                        page + f'?page={self.page_count}'
                    ).context['page_obj']
                )
                self.assertEqual(
                    response_next_page,
                    self.page_size
                )
