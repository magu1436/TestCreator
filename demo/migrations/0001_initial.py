from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='DemoInitialization',
            fields=[
                ('key', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
