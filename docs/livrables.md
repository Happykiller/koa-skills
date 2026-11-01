# Génération des quatre livrables

`python3 outils/livrables.py chantier.json --output docs/chantiers/exemple`

Le registre `chantier.json` doit fournir `name`, et les tableaux `missions`, `decisions`, `observations`, `capabilities`.

- `missions` : `id`, `owner`, `state`, `criteria`, `evidence`, `unverified`
- `decisions` : `decision`, `reason`
- `observations` : `id`, `evidence`, `cause`, `scope`, `action`
- `capabilities` : `name`, `state`, `usage`, `limits`

Le générateur est **déterministe** : il assemble seulement les données déclarées, sans interpréter les transcripts ni certifier les faits. Un champ absent dans une ligne apparaît comme « Non renseigné ». L'agent responsable valide les états et preuves avant publication.

La note fonctionnelle liste les capacités marquées `delivered` comme disponibles ; toutes les autres sont explicitement « Non livré ». Le générateur peut produire un brouillon avant l'ordre de livraison, mais ne doit pas être assimilé à une autorisation de livrer.

Le Gantt Mermaid, la mise en forme HTML et les liens de preuves sont à conserver ou enrichir au QG lorsqu'ils sont nécessaires : ce moteur minimal n'en génère pas. Il ne remplace pas une revue humaine des quatre vues.
