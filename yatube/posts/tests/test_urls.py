from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.anothe_user = User.objects.create_user(username='anothe_auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
            description='Описание',
        )

    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_accordance_url_and_name(self):
        """Проверка на соответствие url-name"""
        accords_url: list = [
            (reverse('posts:index'), '/'),
            (reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ), f'/group/{self.group.slug}/'),
            (reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ), f'/profile/{self.user.username}/'),
            (reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ), f'/posts/{self.post.id}/'),
            (reverse('posts:post_create'), '/create/'),
            (reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ), f'/posts/{self.post.id}/edit/'),
        ]
        for name_url, accord in accords_url:
            with self.subTest(name_url=name_url):
                self.assertEqual(name_url, accord)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        templates_url_names: list = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ), 'posts/group_list.html'),
            (reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ), 'posts/profile.html'),
            (reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ), 'posts/post_detail.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ), 'posts/create_post.html'),
        ]
        for adress, template in templates_url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_authorized_client(self):
        """Проверка доступа пользователя"""
        pages_status: list = [
            (reverse('posts:index'), HTTPStatus.OK, False),
            (reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ), HTTPStatus.OK, False),
            (reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ), HTTPStatus.OK, False),
            (reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ), HTTPStatus.OK, False),
            ((reverse('posts:post_create')), HTTPStatus.OK, True),
            ((reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            )), HTTPStatus.OK, True),
            (('/unexisting_page/'), HTTPStatus.NOT_FOUND, False)
        ]
        for page, status_code, autorized in pages_status:
            with self.subTest(page=page):
                if autorized:
                    response = self.authorized_client.get(page)
                else:
                    response = self.client.get(page)
                self.assertEqual(response.status_code, status_code)

    def test_urls_redirect_anonymous(self):
        """Редирект неавторизованного пользователя"""
        url_log = reverse('users:login')
        url_create = reverse('posts:post_create')
        url_edit = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        url_create_redirect = f'{url_log}?next={url_create}'
        url_edit_redirect = f'{url_log}?next={url_edit}'
        urls = [
            (reverse('posts:post_create'), url_create_redirect),
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ), url_edit_redirect)
        ]
        for url, value in urls:
            response = self.client.get(url)
            self.assertRedirects(response, value)

    def test_urls_redirect_not_author_of_edit(self):
        """Редирект не автора со страницы редактирования"""
        self.authorized_client.force_login(self.anothe_user)
        url_request = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        )
        url_redirect = reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        )
        response_anothe_author = self.authorized_client.get(url_request)
        self.assertRedirects(response_anothe_author, url_redirect)
