from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0012_statetransitionlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='statetransitionlog',
            name='to_workflow_state',
            field=models.CharField(
                blank=True,
                choices=[
                    ('IFP_CANDIDATE_REVIEW', 'Révision des candidats IFP'),
                    ('REGULAR_REVIEW_PENDING', 'Révision régulière en attente'),
                    ('READY_FOR_FINALIZATION', 'Prêt pour finalisation'),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='statetransitionlog',
            name='to_final_april_state',
            field=models.CharField(
                blank=True,
                choices=[
                    ('APRIL_FINAL_PROMOTE_REGULAR', 'Promotion régulière'),
                    ('APRIL_FINAL_PROMOTE_WITH_SUMMER', "Promotion avec cours d'été"),
                    ('APRIL_FINAL_HOLDBACK', 'Doublement'),
                    ('APRIL_FINAL_IFP_N', 'IFP N'),
                    ('APRIL_FINAL_IFP_N_MINUS_1', 'IFP N-1'),
                ],
                max_length=50,
                null=True,
            ),
        ),
    ]
