# Generated by Django 5.1.4 on 2025-04-28 13:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MedicalRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_type', models.CharField(choices=[('lab_report', 'Laboratory Report'), ('prescription', 'Prescription'), ('medical_image', 'Medical Image'), ('diagnosis', 'Diagnosis'), ('treatment_plan', 'Treatment Plan'), ('surgery_record', 'Surgery Record'), ('allergy_record', 'Allergy Record'), ('vaccination', 'Vaccination Record'), ('other', 'Other')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('record_date', models.DateField()),
                ('file', models.FileField(blank=True, null=True, upload_to='medical_records/')),
                ('is_private', models.BooleanField(default=False, help_text='If marked private, only the patient and their doctors can view')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='records_created', to='accounts.doctorprofile')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medical_records', to='accounts.patientprofile')),
            ],
            options={
                'ordering': ['-record_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('dosage_instructions', models.TextField()),
                ('refills_allowed', models.PositiveSmallIntegerField(default=0)),
                ('medical_record', models.OneToOneField(limit_choices_to={'record_type': 'prescription'}, on_delete=django.db.models.deletion.CASCADE, related_name='prescription', to='medical_records.medicalrecord')),
                ('prescribed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prescriptions', to='accounts.doctorprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Medication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('dosage', models.CharField(max_length=100)),
                ('frequency', models.CharField(max_length=100)),
                ('duration', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('prescription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medications', to='medical_records.prescription')),
            ],
        ),
    ]
