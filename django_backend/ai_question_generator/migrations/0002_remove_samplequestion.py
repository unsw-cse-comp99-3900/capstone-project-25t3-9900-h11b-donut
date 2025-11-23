# Generated migration to remove SampleQuestion model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_question_generator', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SampleQuestion',
        ),
    ]
