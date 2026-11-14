from django.db import migrations, models


def make_existing_readers_contributors(apps, schema_editor):
    Profile = apps.get_model('core', 'Profile')
    Profile.objects.filter(role='reader').update(role='author')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_article_cover_image_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.CharField(
                choices=[('reader', 'Reader'), ('author', 'Author'), ('editor', 'Editor')],
                default='author',
                max_length=12,
            ),
        ),
        migrations.RunPython(make_existing_readers_contributors, migrations.RunPython.noop),
    ]
