#!/usr/bin/env python3
"""
Generate every data/asset file for both mod targets from spec/recipes.py.

    python tools/generate.py            # write files
    python tools/generate.py --check    # write nothing, fail if generated files are out of date

Requires Pillow for the item textures, which tools/textures.py draws (pip install pillow).
"""
import argparse
import io
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "spec"))
import recipes as spec  # noqa: E402
import textures as art  # noqa: E402

# 1.20.1 Create (6.0.x Forge) uses the legacy JSON dialect, 1.21.1 uses the codec-based one.
TARGETS = {
    "forge-1.20.1": {"recipe_dir": "recipes", "legacy": True, "pack_format": 15},
    "neoforge-1.21.1": {"recipe_dir": "recipe", "legacy": False, "pack_format": 34},
}

FLUID_AMOUNT_MB = 250  # one bottle on Forge / NeoForge
JAVA_PKG = "src/main/java/dev/hackerman/exposurecreate"


# ---------------------------------------------------------------- JSON dialect helpers

def item_stack(t, item_id, count=None):
    """A result / output stack."""
    out = {"item": item_id} if t["legacy"] else {"id": item_id}
    if count and count > 1:
        out["count"] = count
    return out


def ingredient(spec_str):
    """'ns:item' -> {"item"}, '#ns:tag' -> {"tag"} (identical in both dialects)."""
    if spec_str.startswith("#"):
        return {"tag": spec_str[1:]}
    return {"item": spec_str}


def potion_fluid(t, potion_id, bottles=None):
    amount = FLUID_AMOUNT_MB * (bottles or spec.FILL_BOTTLES)
    if t["legacy"]:
        return {"fluid": "create:potion", "amount": amount,
                "nbt": {"Potion": potion_id, "Bottle": "REGULAR"}}
    return {
        "type": "fluid_stack",
        "fluid": "create:potion",
        "amount": amount,
        "components": {
            "create:potion_fluid_bottle_type": "regular",
            "minecraft:potion_contents": {"potion": potion_id},
        },
    }


def water_fluid(t):
    amount = FLUID_AMOUNT_MB * spec.MIXING_FLUID_BOTTLES
    if t["legacy"]:
        return {"fluid": "minecraft:water", "amount": amount}
    return {"type": "neoforge:single", "fluid": "minecraft:water", "amount": amount}


# ---------------------------------------------------------------- recipe builders

def step_json(t, step, transitional_id):
    kind = step[0]
    held = {"item": transitional_id}
    out = [item_stack(t, transitional_id)]
    if kind == "deploy":
        return {"type": "create:deploying", "ingredients": [held, {"item": step[1]}], "results": out}
    if kind == "deploy_tag":
        return {"type": "create:deploying", "ingredients": [held, {"tag": step[1]}], "results": out}
    if kind == "fill":
        return {"type": "create:filling", "ingredients": [held, potion_fluid(t, step[1])], "results": out}
    if kind == "press":
        return {"type": "create:pressing", "ingredients": [held], "results": out}
    if kind == "cut":
        return {"type": "create:cutting", "ingredients": [held], "results": out}
    raise ValueError(f"unknown step kind: {kind}")


def sequenced_json(t, r):
    transitional_id = f"{spec.MOD_ID}:{r['transitional']}"
    body = {
        "type": "create:sequenced_assembly",
        "ingredient": {"item": r["start"]},
        "loops": 1,
        "results": [item_stack(t, r["result"])],
        "sequence": [step_json(t, s, transitional_id) for s in r["steps"]],
    }
    body["transitionalItem" if t["legacy"] else "transitional_item"] = item_stack(t, transitional_id)
    return body


def mechanical_json(t, r):
    body = {
        "type": "create:mechanical_crafting",
        "key": {k: ingredient(v) for k, v in r["key"].items()},
        "pattern": r["pattern"],
        "result": item_stack(t, r["result"]),
    }
    body["acceptMirrored" if t["legacy"] else "accept_mirrored"] = True
    return body


def compacting_json(t, r):
    return {
        "type": "create:compacting",
        "ingredients": [ingredient(i) for i in r["ingredients"]],
        "results": [item_stack(t, r["result"])],
    }


def mixing_json(t, r):
    ings = [ingredient(i) for i in r["ingredients"]]
    for f in r["fluids"]:
        ings.append(water_fluid(t) if f == "water" else potion_fluid(t, f, spec.MIXING_FLUID_BOTTLES))
    return {
        "type": "create:mixing",
        "ingredients": ings,
        "results": [item_stack(t, r["result"], r["count"])],
    }


BUILDERS = {"sequenced": sequenced_json, "mechanical": mechanical_json,
            "compacting": compacting_json, "mixing": mixing_json}


# ---------------------------------------------------------------- validation

def validate():
    seen_ids = {}
    seen_first = {}
    for r in spec.RECIPES:
        if r["group"] not in spec.GROUPS:
            raise SystemExit(f"{r['result']}: unknown group {r['group']!r}")
        if r["kind"] not in BUILDERS:
            raise SystemExit(f"{r['result']}: unknown kind {r['kind']!r}")
        if r["result"] in seen_ids:
            raise SystemExit(f"duplicate recipe id {r['result']} (groups {seen_ids[r['result']]}, {r['group']})")
        seen_ids[r["result"]] = r["group"]

        if r["kind"] == "sequenced":
            if r["transitional"] not in spec.INCOMPLETE_ITEMS:
                raise SystemExit(f"{r['result']}: transitional '{r['transitional']}' not in INCOMPLETE_ITEMS")
            if not r["steps"]:
                raise SystemExit(f"{r['result']}: empty sequence")
            key = (r["start"], r["steps"][0])
            if key in seen_first:
                raise SystemExit(
                    f"{r['result']} and {seen_first[key]} share start item {r['start']} AND first step "
                    f"{r['steps'][0]}; Create could not tell them apart. Give one a distinguishing first step."
                )
            seen_first[key] = r["result"]
        if r["kind"] == "mixing" and not 1 <= len(r["fluids"]) <= 2:
            raise SystemExit(f"{r['result']}: mixing supports 1-2 fluids, got {len(r['fluids'])}")
        if r["kind"] == "mechanical":
            width = {len(row) for row in r["pattern"]}
            if len(width) != 1:
                raise SystemExit(f"{r['result']}: mechanical pattern rows differ in width")
            used = {c for row in r["pattern"] for c in row if c != " "}
            if used != set(r["key"]):
                raise SystemExit(f"{r['result']}: pattern chars {sorted(used)} != key {sorted(r['key'])}")

    used_items = {r["transitional"] for r in spec.RECIPES if r["kind"] == "sequenced"}
    unused = set(spec.INCOMPLETE_ITEMS) - used_items
    if unused:
        raise SystemExit(f"incomplete items never used by a recipe: {sorted(unused)}")

    # Java must register exactly the same incomplete items / recipe groups as the spec.
    optional_groups = {g for g in spec.GROUPS if g != "base"}
    for name in TARGETS:
        java_dir = ROOT / name / JAVA_PKG
        items = (java_dir / "ModItems.java").read_text(encoding="utf-8")
        registered = set(re.findall(r'incomplete\("([a-z0-9_]+)"\)', items))
        if registered != set(spec.INCOMPLETE_ITEMS):
            raise SystemExit(
                f"{name}/ModItems.java out of sync with INCOMPLETE_ITEMS: "
                f"missing {sorted(set(spec.INCOMPLETE_ITEMS) - registered)}, "
                f"extra {sorted(registered - set(spec.INCOMPLETE_ITEMS))}")
        packs_file = java_dir / "RecipePacks.java"
        if packs_file.exists():
            groups = set(re.findall(r'new Group\("([a-z0-9_]+)"', packs_file.read_text(encoding="utf-8")))
            if groups != optional_groups:
                raise SystemExit(
                    f"{name}/RecipePacks.java out of sync with GROUPS: "
                    f"missing {sorted(optional_groups - groups)}, extra {sorted(groups - optional_groups)}")
            text = packs_file.read_text(encoding="utf-8")
            for g in optional_groups:
                want = spec.GROUPS[g][0]
                m = re.search(rf'new Group\("{g}",\s*"[^"]*",\s*List\.of\(([^)]*)\)', text)
                have = re.findall(r'"([a-z0-9_]+)"', m.group(1)) if m else None
                if have != want:
                    raise SystemExit(f"{name}/RecipePacks.java: group {g} required mods {have} != spec {want}")


# ---------------------------------------------------------------- output

def dump(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def build_target(t):
    """Return {relative_path: bytes} for one target (everything except textures)."""
    files = {}
    mod = spec.MOD_ID

    for r in spec.RECIPES:
        ns, path = r["result"].split(":")
        base = "" if r["group"] == "base" else f"resourcepacks/{r['group']}/"
        files[f"{base}data/{ns}/{t['recipe_dir']}/{path}.json"] = dump(BUILDERS[r["kind"]](t, r)).encode()

    for group, (_, title) in spec.GROUPS.items():
        if group == "base":
            continue
        files[f"resourcepacks/{group}/pack.mcmeta"] = dump(
            {"pack": {"description": title, "pack_format": t["pack_format"]}}).encode()

    files[f"assets/{mod}/lang/en_us.json"] = dump(
        {f"item.{mod}.{k}": v for k, v in spec.INCOMPLETE_ITEMS.items()}).encode()
    # One sprite per assembly stage. The item model itself is stage 0; overrides swap in the later stages
    # as Create's assembly progress (0..1, exposed by ClientSetup.java) passes i / stage count.
    for k in spec.INCOMPLETE_ITEMS:
        count = len(art.stages(k))
        for i in range(count):
            model = {"parent": "item/generated", "textures": {"layer0": f"{mod}:item/{k}_{i}"}}
            if i == 0:
                model["overrides"] = [
                    # Nudged down so a progress of exactly i / count never lands on the wrong side.
                    {"predicate": {f"{mod}:progress": round(j / count - 0.005, 4)}, "model": f"{mod}:item/{k}_{j}"}
                    for j in range(1, count)]
            files[f"assets/{mod}/models/item/{k if i == 0 else f'{k}_{i}'}.json"] = dump(model).encode()

    files["pack.mcmeta"] = dump(
        {"pack": {"description": spec.GROUPS["base"][1], "pack_format": t["pack_format"]}}).encode()
    return files


def build_textures():
    out = {}
    for k in spec.INCOMPLETE_ITEMS:
        for i, px in enumerate(art.stages(k)):
            buf = io.BytesIO()
            art.to_image(px).save(buf, format="PNG", optimize=True)
            out[f"assets/{spec.MOD_ID}/textures/item/{k}_{i}.png"] = buf.getvalue()
    return out


def same_file(path, data):
    """Byte compare, except PNGs: compare pixels so a different Pillow version is not reported as stale."""
    if not path.exists():
        return False
    if path.suffix != ".png":
        return path.read_bytes() == data
    from PIL import Image

    return Image.open(path).convert("RGBA").tobytes() == Image.open(io.BytesIO(data)).convert("RGBA").tobytes()


# 100% generated: wiped and rewritten on every run, and --check rejects anything extra in them.
GENERATED_DIRS = ("data", "resourcepacks", f"assets/{spec.MOD_ID}/models", f"assets/{spec.MOD_ID}/textures")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    validate()
    textures = build_textures()
    stale = []

    for name, t in TARGETS.items():
        res = ROOT / name / "src" / "main" / "resources"
        files = build_target(t)
        files.update(textures)

        if args.check:
            for p, data in files.items():
                if not same_file(res / p, data):
                    stale.append(f"{name}/{p}")
            # Also catch leftovers: generated dirs must contain exactly the expected files.
            for sub in GENERATED_DIRS:
                root = res / sub
                if root.exists():
                    for f in root.rglob("*"):
                        if f.is_file() and f.relative_to(res).as_posix() not in files:
                            stale.append(f"{name}/{f.relative_to(res).as_posix()} (unexpected)")
            continue

        for sub in GENERATED_DIRS:
            shutil.rmtree(res / sub, ignore_errors=True)
        for p, data in files.items():
            f = res / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        print(f"{name}: wrote {len(files)} files")

    if args.check:
        if stale:
            print("OUT OF DATE (run python tools/generate.py):\n  " + "\n  ".join(stale))
            sys.exit(1)
        print("generated files are up to date")


if __name__ == "__main__":
    main()
