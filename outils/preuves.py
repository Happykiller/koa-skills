#!/usr/bin/env python3
"""Registre de preuves conservateur : aucune preuve ne vaut hors de son contexte exact."""
import argparse
import hashlib
import json
from pathlib import Path

def fingerprint(paths):
    h = hashlib.sha256()
    for p in sorted(map(Path, paths), key=lambda x: str(x)):
        if not p.is_file():
            raise ValueError(f"fichier manquant : {p}")
        h.update(str(p).encode()); h.update(b"\0"); h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()

def context(args):
    return {"commit": args.commit, "environment": args.environment,
            "config": args.config, "dependencies": args.dependencies,
            "files_sha256": fingerprint(args.files)}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["record", "check"])
    p.add_argument("--registry", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--environment", required=True)
    p.add_argument("--config", required=True, help="empreinte de configuration fournie par la CI")
    p.add_argument("--dependencies", required=True, help="empreinte des dépendances")
    p.add_argument("--files", nargs="+", required=True)
    p.add_argument("--result", choices=["PASS", "FAIL", "INCONCLUSIVE"])
    p.add_argument("--command")
    a = p.parse_args()
    try:
        c = context(a)
        path = Path(a.registry)
        registry = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if a.action == "record":
            if not a.result or not a.command:
                p.error("record nécessite --result et --command")
            registry[a.id] = {"context": c, "result": a.result, "command": a.command}
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(registry, indent=2, ensure_ascii=False, sort_keys=True)+"\n", encoding="utf-8")
            print(json.dumps({"id": a.id, "status": "RECORDED", "result": a.result}))
        else:
            item = registry.get(a.id)
            status = ("MISSING" if item is None else
                      "INVALIDATED" if item.get("context") != c else
                      "REUSABLE" if item.get("result") == "PASS" else "NOT_PASSED")
            print(json.dumps({"id": a.id, "status": status}))
            if status != "REUSABLE":
                raise SystemExit(2)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({"status":"ERROR", "detail":str(e)}))
        raise SystemExit(2)

if __name__ == "__main__":
    main()
