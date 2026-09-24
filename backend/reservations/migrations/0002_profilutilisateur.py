import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfilUtilisateur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.FileField(blank=True, null=True, upload_to='profils/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('utilisateur', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profil_application', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'profil_utilisateur'},
        ),
    ]
