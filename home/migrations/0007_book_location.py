# Generated by Django 5.1.6 on 2025-04-06 23:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0006_book_book_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="location",
            field=models.CharField(
                blank=True, default="N/A", max_length=100, null=True
            ),
        ),
    ]
