import django.db.models.deletion
import reservations.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notifications',
            fields=[
                ('id_notification', models.AutoField(primary_key=True, serialize=False)),
                ('destinataire', models.CharField(max_length=150)),
                ('type_notification', models.CharField(max_length=50)),
                ('objet', models.CharField(blank=True, max_length=255, null=True)),
                ('statut', models.CharField(blank=True, max_length=50, null=True)),
                ('date_envoi', models.DateTimeField(blank=True, null=True)),
                ('message_erreur', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'db_table': 'notifications',
            },
        ),
        migrations.CreateModel(
            name='Parametres',
            fields=[
                ('id_parametre', models.AutoField(primary_key=True, serialize=False)),
                ('cle', models.CharField(max_length=100, unique=True)),
                ('valeur', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Paramètre',
                'verbose_name_plural': 'Paramètres',
                'db_table': 'parametres',
            },
        ),
        migrations.CreateModel(
            name='Participants',
            fields=[
                ('id_participant', models.AutoField(primary_key=True, serialize=False)),
                ('nom', models.CharField(blank=True, max_length=150, null=True)),
                ('email', models.CharField(max_length=150)),
            ],
            options={
                'verbose_name': 'Participant',
                'verbose_name_plural': 'Participants',
                'db_table': 'participants',
            },
        ),
        migrations.CreateModel(
            name='Rappels',
            fields=[
                ('id_rappel', models.AutoField(primary_key=True, serialize=False)),
                ('date_heure_prevue', models.DateTimeField()),
                ('statut', models.CharField(blank=True, max_length=50, null=True)),
                ('date_heure_envoi', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Rappel',
                'verbose_name_plural': 'Rappels',
                'db_table': 'rappels',
            },
        ),
        migrations.CreateModel(
            name='Reservations',
            fields=[
                ('id_reservation', models.AutoField(primary_key=True, serialize=False)),
                ('nom_demandeur', models.CharField(max_length=150)),
                ('email_demandeur', models.CharField(max_length=150)),
                ('objet', models.CharField(max_length=255)),
                ('date_reservation', models.DateField()),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('nombre_participants', models.IntegerField(blank=True, null=True)),
                ('statut', models.CharField(blank=True, max_length=50, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('date_creation', models.DateTimeField(blank=True, null=True)),
                ('date_modification', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Réservation',
                'verbose_name_plural': 'Réservations',
                'db_table': 'reservations',
            },
        ),
        migrations.CreateModel(
            name='Salles',
            fields=[
                ('id_salle', models.AutoField(primary_key=True, serialize=False)),
                ('nom_salle', models.CharField(max_length=100)),
                ('localisation', models.CharField(blank=True, max_length=150, null=True)),
                ('etage', models.CharField(blank=True, max_length=50, null=True)),
                ('capacite', models.IntegerField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Salle',
                'verbose_name_plural': 'Salles',
                'db_table': 'salles',
            },
        ),
        migrations.CreateModel(
            name='Utilisateurs',
            fields=[
                ('id_utilisateur', models.AutoField(primary_key=True, serialize=False)),
                ('nom', models.CharField(max_length=100)),
                ('prenom', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.CharField(max_length=150, unique=True)),
                ('mot_de_passe', models.CharField(max_length=255)),
                ('role', models.CharField(blank=True, max_length=50, null=True)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Utilisateur',
                'verbose_name_plural': 'Utilisateurs',
                'db_table': 'utilisateurs',
            },
        ),
        migrations.CreateModel(
            name='ProfilRH',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'profil_rh',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='SessionRH',
            fields=[
                ('key', models.CharField(default=reservations.models.generate_session_key, editable=False, max_length=40, primary_key=True, serialize=False)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('derniere_activite', models.DateTimeField(auto_now=True)),
                ('profil', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sessions', to='reservations.profilrh')),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions_rh', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'session_rh',
            },
        ),
        # Les tables métier étaient autrefois créées à la main (MySQL) ; elles
        # sont maintenant créées par ces migrations. Une base déjà en service
        # n'est pas concernée : cette migration y est déjà enregistrée.
        migrations.AddField(
            model_name='reservations',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                db_column='created_by_id',
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reservations_creees',
                to='reservations.profilrh',
            ),
        ),
        migrations.AddField(
            model_name='reservations',
            name='updated_by',
            field=models.ForeignKey(
                blank=True,
                db_column='updated_by_id',
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reservations_modifiees',
                to='reservations.profilrh',
            ),
        ),
        migrations.AddField(
            model_name='reservations',
            name='cancelled_by',
            field=models.ForeignKey(
                blank=True,
                db_column='cancelled_by_id',
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reservations_annulees',
                to='reservations.profilrh',
            ),
        ),
        migrations.AddField(
            model_name='reservations',
            name='id_salle',
            field=models.ForeignKey(db_column='id_salle', on_delete=django.db.models.deletion.PROTECT, to='reservations.salles'),
        ),
        migrations.AddField(
            model_name='reservations',
            name='id_utilisateur',
            field=models.ForeignKey(db_column='id_utilisateur', on_delete=django.db.models.deletion.PROTECT, to='reservations.utilisateurs'),
        ),
        migrations.AddField(
            model_name='participants',
            name='id_reservation',
            field=models.ForeignKey(db_column='id_reservation', on_delete=django.db.models.deletion.CASCADE, to='reservations.reservations'),
        ),
        migrations.AddField(
            model_name='rappels',
            name='id_reservation',
            field=models.ForeignKey(db_column='id_reservation', on_delete=django.db.models.deletion.CASCADE, to='reservations.reservations'),
        ),
        migrations.AddField(
            model_name='notifications',
            name='id_reservation',
            field=models.ForeignKey(db_column='id_reservation', on_delete=django.db.models.deletion.CASCADE, to='reservations.reservations'),
        ),
    ]
