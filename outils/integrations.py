#!/usr/bin/env python3
"""Contrôle des dépendances de missions et déclenchement de jalons d'intégration."""
import argparse
import json
from pathlib import Path

def evaluate(plan):
    missions = plan["missions"]
    if not isinstance(missions, dict):
        raise ValueError("missions doit être un objet")
    events = []
    for gate in plan["integrations"]:
        a, b = gate["missions"]
        if a == b or a not in missions or b not in missions:
            raise ValueError(f"missions inconnues ou identiques : {a}, {b}")
        if not gate.get("contract") or not gate.get("owner") or not gate.get("command"):
            raise ValueError("contrat, responsable et commande sont obligatoires")
        if not gate.get("id"):
            raise ValueError("identifiant du jalon obligatoire")
        ready = all(missions[m].get("state") == "accepted" for m in (a,b))
        proof = gate.get("proof", {})
        status = ("BLOCKED" if not ready else "PASSED" if
                  proof.get("result") == "PASS" and proof.get("commit") == gate.get("commit") and
                  bool(gate.get("commit")) else "ACTION_REQUIRED")
        events.append({"id":gate["id"],"status":status,"owner":gate["owner"],
                       "command":gate["command"] if ready else None,
                       "contract":gate["contract"],"missions":[a,b]})
    return events

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("plan", type=Path)
    a = p.parse_args()
    try:
        events = evaluate(json.loads(a.plan.read_text(encoding="utf-8")))
        print(json.dumps({"integrations":events}, indent=2, ensure_ascii=False))
        if any(x["status"] != "PASSED" for x in events):
            raise SystemExit(2)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as e:
        print(json.dumps({"error":str(e)}))
        raise SystemExit(2)

if __name__ == "__main__":
    main()
