from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст для теста длиннее 15 символов',
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
            description='Описание',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        equal_str = [
            (self.group.title, str(self.group)),
            (self.post.text[:Post.NUM_CHAR_POST], str(self.post)),
        ]
        for response, str_model in equal_str:
            with self.subTest(response=response):
                self.assertEqual(response, str_model)
