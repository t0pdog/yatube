# Generated by Django 2.2.16 on 2022-05-27 21:57

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20220527_1858'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(_negated=True, author=django.db.models.expressions.F('user')), name='author_not_user'),
        ),
    ]
