# Generated by Django 3.2.16 on 2023-10-18 18:31

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20231016_1339'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='Вы не можете подписаться на себя!',
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='Вы уже подписаны!'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(('user', django.db.models.expressions.F('author')), _negated=True), name='Вы не можете подписаться на себя!'),
        ),
    ]