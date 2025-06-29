# Generated by Django 5.1.6 on 2025-05-31 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("solarapp", "0013_remove_userprofile_approved"),
    ]

    operations = [
        migrations.AlterField(
            model_name="role",
            name="name",
            field=models.CharField(
                choices=[
                    ("Admin", "Admin"),
                    ("Drone controller", "Drone controller"),
                    ("Admin solar", "Admin solar"),
                    ("Data analyst", "Data analyst"),
                ],
                max_length=50,
                unique=True,
            ),
        ),
    ]
