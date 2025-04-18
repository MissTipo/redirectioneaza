# Generated by Django 5.1.4 on 2024-12-19 09:04

import django.db.models.deletion
import tinymce.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Section",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="Title")),
                ("order", models.IntegerField(default=0, verbose_name="Order")),
            ],
            options={
                "ordering": ["order", "title"],
            },
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="Question")),
                ("answer", tinymce.models.HTMLField(verbose_name="Answer")),
                ("order", models.IntegerField(default=0, verbose_name="Order")),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="frequent_questions.section",
                    ),
                ),
            ],
            options={
                "ordering": ["order", "title"],
            },
        ),
    ]
