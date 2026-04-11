from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("school", "0008_meqreference"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="stream",
            field=models.CharField(
                choices=[
                    ("REGULAR", "Régulier"),
                    ("ZENITH", "Zénith"),
                    ("IFP", "IFP"),
                    ("ACCUEIL", "Accueil ILSS"),
                ],
                default="REGULAR",
                help_text="Filière du cours (Régulier, Zénith, IFP, Accueil)",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="category",
            field=models.CharField(
                choices=[
                    ("CORE", "Matière de base"),
                    ("PARCOURS", "Parcours"),
                    ("OPTION", "Option"),
                ],
                default="CORE",
                help_text="Catégorie pédagogique du cours",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="cycle",
            field=models.CharField(
                choices=[
                    ("PREMIER", "Premier cycle"),
                    ("DEUXIEME", "Deuxième cycle"),
                    ("ACCUEIL", "Accueil"),
                ],
                default="PREMIER",
                help_text="Cycle scolaire (Premier, Deuxième, Accueil)",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="group_type",
            field=models.CharField(
                choices=[
                    ("OPEN", "Groupe ouvert"),
                    ("CLOSED", "Groupe fermé"),
                ],
                default="CLOSED",
                help_text="Type de groupe (fermé ou ouvert)",
                max_length=10,
            ),
        ),
    ]
