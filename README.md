# Butin de Raid

Outil de conseil de butin pour une guilde WoW Classic (et Forever). Les officiers voient ce que chaque personnage a reçu, sur quel emplacement, et à qui donner le prochain objet.

- **Site** : https://extrym.github.io/butin-raid/ (connexion Discord, accès donné par un admin).
- **Pour qui** : tous les rôles (Tank, Heal, CAC, Caster, Distance), roster 20 et deux rosters 10, mains et rerolls.
- **Catalogue** : 1 908 objets Classic (raids, donjons de fin de jeu, artisanat, quêtes, niveau 55+, rare ou mieux) et 855 objets Forever **provisoires** tirés du client bêta. On peut aussi ajouter des objets à la main.

## Utilisation

### Avant le premier raid

1. **Roster → Joueurs** : une ligne par personne du Discord, avec son rôle (Membre, Roster, Admin).
2. **Roster → Personnages** : pour chaque joueur, son main et ses rerolls, avec la classe, la **spé** (elle détermine le rôle) et les groupes (Roster 20, Roster 10 A, Roster 10 B).
3. **Roster → Règle de comptage** : coche « Les loots des rerolls comptent pour le joueur » si un joueur servi sur son reroll doit passer après les autres.

### Pendant le raid : attribuer un objet

1. Onglet **Attribuer un objet**.
2. Choisis le raid (il reste en mémoire), puis clique sur le boss. Ou tape 3 lettres du nom de l'objet et appuie sur Entrée.
3. Les candidats s'affichent, filtrés par classe et par rôle, du moins servi au plus servi. Clique sur un bouton de rôle pour l'ajouter ou le retirer.
4. Choisis le type (BiS, Spé principale, Hors-spé), puis **Donner**. Un bouton « Annuler » reste affiché quelques secondes.

Pour que le loot soit rattaché à un groupe, choisis le groupe (Roster 20, 10 A, 10 B) dans le filtre en haut avant d'attribuer.

**Ordre de suggestion** :
1. Classe et rôle qui conviennent à l'objet.
2. N'a pas déjà l'objet.
3. Le moins de loots principaux (BiS et spé principale) sur la période choisie, autres personnages compris selon la règle de comptage.
4. Le dernier loot le plus ancien.
5. Raider avant Trial.

En cas d'égalité, tous les ex æquo sont signalés. La décision reste au conseil.

### Après le raid : qui a eu quoi

- **Tableau des loots** : une ligne par personnage, une colonne par emplacement (Tête, Mains, Jambes, Armes…). Survole un chiffre pour voir les objets.
- **Fiche personnage** : clique sur un nom pour voir ses totaux et ses objets rangés par emplacement. Coche « Inclure ses autres personnages » pour tout le joueur.
- **Historique** : tous les loots, filtrables par personnage ou par recherche. Un loot peut être supprimé.
- Les filtres du haut (version, groupe, période) s'appliquent partout.

### Catalogue

- Recherche et filtre par source.
- Survole un objet pour voir ses caractéristiques. Le lien ouvre la fiche Wowhead.
- Ajoute les objets Forever avec le formulaire (nom, raid, boss, emplacement, rôles, classes).

## Hébergement et accès

- **Site** : https://extrym.github.io/butin-raid/ (GitHub Pages).
- **Données** : base Supabase (roster, personnages, loots, réglages). Elles ne sont jamais dans ce dépôt.
- **Connexion** : avec Discord. Sans accès, on ne voit que l'écran de connexion.
- **Niveaux** : *Membre* lit le roster et les loots, *Officier* attribue et modifie, *Admin* gère les accès (onglet **Accès**, visible des admins seulement).
- **Sécurité** : les règles sont appliquées par la base elle-même (Row Level Security), pas par la page. La clé Supabase présente dans `index.html` est une clé publique prévue pour ça.
- **Export** : onglet Historique → **Exporter CSV** (s'ouvre dans Excel ou Google Sheets) ou **Exporter JSON** (sauvegarde complète).
- **Veille** : l'offre gratuite de Supabase met le projet en pause après 7 jours sans visite. Il se relance d'un clic depuis le tableau de bord Supabase, sans perte de données.

Le schéma de la base et ses règles d'accès sont dans `supabase/schema.sql`.

## Contenu du dépôt

| Chemin | Rôle |
|---|---|
| `index.html` | Le site complet (HTML, CSS, JavaScript) |
| `data/items-classic.json` | Catalogue Classic généré |
| `scripts/build_items.py` | Génère le catalogue Classic |
| `scripts/build_forever.py` | Génère le catalogue Forever provisoire |
| `data/items-forever.json` | Catalogue Forever généré |
| `supabase/schema.sql` | Tables et règles d'accès de la base |
| `source/` | Base source brute (non versionnée, 35 Mo) |

### Régénérer le catalogue

```sh
mkdir -p source
curl -L -o source/items-classic.json https://raw.githubusercontent.com/nexus-devs/wow-classic-items/master/data/json/data.json
curl -L -o source/zones.json https://raw.githubusercontent.com/nexus-devs/wow-classic-items/master/data/json/zones.json
python3 scripts/build_items.py
```

Le script garde les objets Classic de qualité rare ou mieux, niveau requis 55+ (ou niveau d'objet 57+), venant d'un raid, d'un donjon de fin de jeu, de l'artisanat ou d'une quête. Il déduit aussi les classes qui portent chaque objet et les rôles intéressés d'après ses caractéristiques.

### Catalogue Forever (provisoire)

```sh
mkdir -p source/forever
curl -L -o source/forever/db.json https://raw.githubusercontent.com/ElliotWood/Forever/HEAD/assets/database/db.json
python3 scripts/build_forever.py
```

Garde les objets nouveaux de Forever (identifiant ≥ 250000), rare ou mieux, niveau d'objet 55+. Les caractéristiques viennent du client bêta et peuvent changer. La source de la plupart des objets (boss, réputation) est inconnue avant la sortie : les raids ouvrent le 9 décembre 2026. Relance le script après les mises à jour du projet source.

## Crédits

Données d'objets : [nexus-devs/wow-classic-items](https://github.com/nexus-devs/wow-classic-items) (licence MIT) pour Classic, [ElliotWood/Forever](https://github.com/ElliotWood/Forever) (licence MIT) pour Forever.
