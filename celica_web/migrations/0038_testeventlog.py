# Generated by Django 5.1.7 on 2025-07-19 21:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celica_web', '0037_update_specialite_mixte_to_autre'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestEventLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('test_start', 'Début de test'), ('test_end', 'Fin de test'), ('question_view', 'Visualisation de question'), ('question_answer', 'Réponse à question'), ('question_change', 'Changement de réponse'), ('page_focus', 'Focus sur la page'), ('page_blur', 'Perte de focus'), ('tab_switch', "Changement d'onglet"), ('window_resize', 'Redimensionnement fenêtre'), ('connection_lost', 'Perte de connexion'), ('connection_restored', 'Restauration connexion'), ('timeout_warning', 'Avertissement timeout'), ('violation_detected', 'Violation détectée'), ('auto_save', 'Sauvegarde automatique'), ('manual_save', 'Sauvegarde manuelle'), ('test_pause', 'Pause du test'), ('test_resume', 'Reprise du test'), ('fullscreen_enter', 'Mode plein écran'), ('fullscreen_exit', 'Sortie plein écran'), ('copy_attempt', 'Tentative de copie'), ('paste_attempt', 'Tentative de collage'), ('right_click', 'Clic droit'), ('keyboard_shortcut', 'Raccourci clavier'), ('dev_tools', 'Outils de développement'), ('screenshot_attempt', "Tentative de capture d'écran")], max_length=30)),
                ('event_data', models.JSONField(blank=True, default=dict, help_text="Données supplémentaires de l'événement")),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('question_number', models.PositiveIntegerField(blank=True, help_text='Numéro de la question concernée', null=True)),
                ('session_id', models.CharField(blank=True, help_text='ID de session pour grouper les événements', max_length=100)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('duration', models.PositiveIntegerField(blank=True, help_text='Durée en millisecondes si applicable', null=True)),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_logs', to='celica_web.test')),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': "Journal d'événement de test",
                'verbose_name_plural': "Journaux d'événements de test",
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['test', 'utilisateur', 'timestamp'], name='celica_web__test_id_c337fa_idx'), models.Index(fields=['event_type', 'timestamp'], name='celica_web__event_t_4da1f9_idx'), models.Index(fields=['session_id'], name='celica_web__session_7bb80d_idx')],
            },
        ),
    ]
