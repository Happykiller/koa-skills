#!/usr/bin/env python3
"""Génération déterministe des quatre livrables depuis un registre JSON."""
import argparse
import json
from pathlib import Path

def clean(value):
    return str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")

def rows(items, keys):
    return "\n".join("| " + " | ".join(clean(item.get(key, "Non renseigné")) for key in keys) + " |" for item in items)

def render(data):
    required = ("name", "missions", "decisions", "observations", "capabilities", "gantt")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError("champs manquants : " + ", ".join(missing))
    for key in required[1:]:
        if not isinstance(data[key], list):
            raise ValueError(f"{key} doit être une liste")
    if not isinstance(data["gantt"], str) or not data["gantt"].lstrip().startswith("gantt"):
        raise ValueError("gantt doit contenir un diagramme Mermaid gantt")
    name = clean(data["name"])
    missions = data["missions"]
    plan = (f"# Plan — {name}\n\n| Mission | Responsable | État | Critères | Preuves |\n"
            "|---|---|---|---|---|\n" + rows(missions, ["id","owner","state","criteria","evidence"]) + "\n\n## Gantt\n\n```mermaid\n" + data["gantt"] + "\n```\n")
    bilan = (f"# Bilan technico-fonctionnel — {name}\n\n## Missions\n\n"
             "| Mission | État | Preuves | Non vérifié |\n|---|---|---|---|\n" +
             rows(missions, ["id","state","evidence","unverified"]) +
             "\n\n## Décisions\n\n| Décision | Motif |\n|---|---|\n" +
             rows(data["decisions"], ["decision","reason"]) + "\n")
    rex = (f"# Retour d'expérience — {name}\n\n| Observation | Preuve | Cause / hypothèse | Portée | Action |\n"
           "|---|---|---|---|---|\n" +
           rows(data["observations"], ["id","evidence","cause","scope","action"]) + "\n")
    delivered = [c for c in data["capabilities"] if c.get("state") == "delivered"]
    pending = [c for c in data["capabilities"] if c.get("state") != "delivered"]
    livraison = (f"# Note de livraison fonctionnelle — {name}\n\n"
                 "Seules les capacités déclarées livrées apparaissent dans la section disponible. "
                 "Le statut doit être vérifié auprès du responsable de livraison.\n\n"
                 "## Disponible\n\n| Fonction | Utilisation | Limites |\n|---|---|---|\n" +
                 rows(delivered, ["name","usage","limits"]) +
                 "\n\n## Non livré\n\n| Fonction | État |\n|---|---|\n" +
                 rows(pending, ["name","state"]) + "\n")
    return {"plan.md":plan, "bilan.md":bilan, "rex.md":rex, "livraison.md":livraison}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("registry", type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    try:
        data = json.loads(a.registry.read_text(encoding="utf-8"))
        documents = render(data)
        a.output.mkdir(parents=True, exist_ok=True)
        for name, content in documents.items():
            (a.output / name).write_text(content, encoding="utf-8")
        print(json.dumps({"documents": list(documents)}))
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
        print(json.dumps({"error":str(e)}))
        raise SystemExit(2)

if __name__ == "__main__":
    main()
