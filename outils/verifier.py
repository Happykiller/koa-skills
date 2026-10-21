#!/usr/bin/env python3
"""Ce que `claude plugin validate` ne voit pas, vérifié avant chaque publication.

- chaque skill a un frontmatter en première ligne, un `name` égal à son dossier, une description ;
- la marketplace liste exactement les plugins du dépôt, sous le nom de leur `plugin.json` ;
- aucun motif de fuite : chemin personnel, jeton, adresse électronique ;
- aucun format pensé pour d'autres outils (le framework est typé Claude).

`--catalogue` imprime le catalogue que KoA embarque (`src/Koa.Core/Librairie/koa-skills.txt`) : une
seule source, une version dérivée par ce script, jamais retouchée à la main.
"""
import io
import json
import os
import re
import sys

RACINE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

FUITES = [
    (r"(?<![\w$])/home/[a-z]", "chemin personnel"),
    (r"[A-Za-z]:\\Users\\", "chemin personnel"),
    (r"\b(ghp|gho|github_pat|sk-ant|xox[bp])[-_][A-Za-z0-9]{8,}", "jeton"),
    (r"[\w.+-]+@[\w-]+\.[\w.]+", "adresse électronique"),
    (r"\bAGENTS\.md\b", "format d'un autre outil"),
]
# Toutes les descriptions de skills sont chargées dans le contexte de chaque session : chaque caractère se
# paie à chaque tour, pour chaque agent. Une description dit quand se déclencher, pas ce que la skill fait
# en détail — le corps est là pour ça (0.3.0 : 24 descriptions, 7 400 caractères).
BUDGET_DESCRIPTION = 260
BUDGET_TOTAL = 6000
DECLENCHEUR = re.compile(r"\bquand\b|\bpar /|\bà déclencher\b", re.I)

# L'adresse d'installation d'un plugin a la forme d'une adresse électronique sans en être une.
FAUX_POSITIFS = re.compile(r"^[a-z0-9-]+@koa-skills$")


def lire(chemin):
    return io.open(chemin, encoding="utf-8").read()


def frontmatter(texte):
    if not texte.startswith("---\n"):
        return None
    fin = texte.find("\n---\n", 4)
    if fin < 0:
        return None
    champs = {}
    for ligne in texte[4:fin].split("\n"):
        m = re.match(r"^([a-z-]+):\s*(.*)$", ligne)
        if m:
            champs[m.group(1)] = m.group(2).strip().strip('"')
    return champs


def plugins():
    marche = json.loads(lire(os.path.join(RACINE, ".claude-plugin", "marketplace.json")))
    return marche, sorted(marche["plugins"], key=lambda p: p["name"])


def verifier():
    fautes, total = [], 0
    marche, entrees = plugins()
    dossiers = sorted(d for d in os.listdir(os.path.join(RACINE, "plugins")))
    noms = sorted(p["name"] for p in entrees)
    if dossiers != noms:
        fautes.append(f"marketplace.json liste {noms}, le dépôt porte {dossiers}")
    for p in entrees:
        manifeste = json.loads(lire(os.path.join(RACINE, p["source"], ".claude-plugin", "plugin.json")))
        if manifeste.get("name") != p["name"]:
            fautes.append(f"{p['name']} : plugin.json s'appelle « {manifeste.get('name')} »")
        if not re.fullmatch(r"\d+\.\d+\.\d+", manifeste.get("version", "")):
            fautes.append(f"{p['name']} : version absente ou non sémantique")
        dossier_skills = os.path.join(RACINE, p["source"], "skills")
        for nom in sorted(os.listdir(dossier_skills)) if os.path.isdir(dossier_skills) else []:
            fm = frontmatter(lire(os.path.join(dossier_skills, nom, "SKILL.md")))
            if fm is None:
                fautes.append(f"{p['name']}:{nom} : pas de frontmatter en première ligne")
                continue
            if fm.get("name") != nom:
                fautes.append(f"{p['name']}:{nom} : name « {fm.get('name')} » différent du dossier")
            description = fm.get("description") or ""
            if not description or len(description) > BUDGET_DESCRIPTION:
                fautes.append(f"{p['name']}:{nom} : description absente ou au-delà de "
                              f"{BUDGET_DESCRIPTION} caractères ({len(description)})")
            elif not DECLENCHEUR.search(description):
                fautes.append(f"{p['name']}:{nom} : la description ne dit pas quand se déclencher "
                              "(« quand : … » ou « par /… »)")
            total += len(description)
    if total > BUDGET_TOTAL:
        fautes.append(f"les descriptions de skills pèsent {total} caractères, au-delà de {BUDGET_TOTAL} : "
                      "chaque session les charge toutes")
    for dossier, _, fichiers in os.walk(RACINE):
        if os.sep + ".git" in dossier + os.sep:
            continue
        for f in fichiers:
            if not f.endswith((".md", ".json", ".py", ".sh", ".yml")):
                continue
            chemin = os.path.join(dossier, f)
            # Ce script et son test portent les motifs et leurs exemples : ce sont les seuls fichiers
            # qui ont le droit de les écrire.
            if os.path.basename(chemin) in ("verifier.py", "test_verifier.py"):
                continue
            texte = lire(chemin)
            for motif, quoi in FUITES:
                for m in re.finditer(motif, texte):
                    if FAUX_POSITIFS.match(m.group(0)):
                        continue
                    fautes.append(f"{os.path.relpath(chemin, RACINE)} : {quoi} « {m.group(0)} »")
    return fautes


def catalogue():
    marche, entrees = plugins()
    lignes = [f"marketplace koa-skills Happykiller/koa-skills v{marche['metadata']['version']}"]
    for p in entrees:
        manifeste = json.loads(lire(os.path.join(RACINE, p["source"], ".claude-plugin", "plugin.json")))
        lignes.append(f"plugin {p['name']} {manifeste['version']}")
        dossier_skills = os.path.join(RACINE, p["source"], "skills")
        for nom in sorted(os.listdir(dossier_skills)) if os.path.isdir(dossier_skills) else []:
            lignes.append(f"skill {p['name']}:{nom}")
    return "\n".join(lignes)


if __name__ == "__main__":
    if "--catalogue" in sys.argv:
        print(catalogue())
        sys.exit(0)
    fautes = verifier()
    for f in fautes:
        print("FAUTE", f)
    print(f"{len(fautes)} faute(s)")
    sys.exit(1 if fautes else 0)
