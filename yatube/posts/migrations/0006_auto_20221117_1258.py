# Generated by Django 2.2.16 on 2022-11-17 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_comments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comments',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата создания'),
        ),
    ]
