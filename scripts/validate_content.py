#!/usr/bin/env python3
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANK = ROOT / "app/src/main/assets/content/english_g5_vso.json"
DICTIONARY = ROOT / "app/src/main/assets/content/dictionary_en.json"
ECONOMY = ROOT / "app/src/main/assets/game/economy.json"
SHOP = ROOT / "app/src/main/assets/game/shop_catalog.json"
REWARDS = ROOT / "app/src/main/assets/game/reward_catalog.json"
MINIGAMES = ROOT / "app/src/main/assets/game/minigames.json"
PLAY_CREDITS = ROOT / "app/src/main/assets/game/play_credits.json"
ATLAS = ROOT / "app/src/main/assets/content/knowledge_atlas.json"
CATALOG = ROOT / "app/src/main/assets/content/catalog.json"
ENTITLEMENTS = ROOT / "app/src/main/assets/commerce/entitlements.json"
TARGETS = ROOT / "app/src/main/assets/content/training_targets.json"
LICENSES = ROOT / "app/src/main/assets/content/licenses.json"
PRODUCTS = ROOT / "app/src/main/assets/commerce/products.json"

def fail(msg):
    print(f"CONTENT ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)

with BANK.open(encoding="utf-8") as f:
    bank = json.load(f)

pack = bank.get("pack")
if not isinstance(pack, dict):
    fail("pack metadata is required")
for field in ("id", "subject", "grade_min", "grade_max", "season", "title", "subtitle"):
    if field not in pack:
        fail(f"pack.{field} is required")

units = bank.get("knowledge_units")
if not isinstance(units, list) or not units:
    fail("knowledge_units must be a non-empty array")

unit_ids = set()
for unit in units:
    uid = unit.get("id")
    if not isinstance(uid, str) or not uid:
        fail("knowledge unit id is required")
    if uid in unit_ids:
        fail(f"duplicate knowledge unit: {uid}")
    unit_ids.add(uid)
    if not isinstance(unit.get("labels"), dict) or not unit["labels"]:
        fail(f"{uid}: labels are required")

questions = bank.get("questions")
if not isinstance(questions, list) or not questions:
    fail("questions must be a non-empty array")

seen = set()
seen_prompts = {}
seen_listening_scripts = {}
seen_audio_paths = {}
dialogues = 0
supported = {"single_choice"}
modes = {"grammar", "reading", "listening", "story"}
skills = set()
listening = 0

for i, q in enumerate(questions):
    where = f"question[{i}]"
    qid = q.get("id")
    if not isinstance(qid, str) or not qid.strip():
        fail(f"{where}: missing id")
    if qid in seen:
        fail(f"{qid}: duplicate id")
    seen.add(qid)

    if q.get("interaction") not in supported:
        fail(f"{qid}: runtime currently supports {sorted(supported)}, got {q.get('interaction')!r}")
    if q.get("mode") not in modes:
        fail(f"{qid}: invalid mode")

    qskills = q.get("skills")
    if not isinstance(qskills, list) or not qskills:
        fail(f"{qid}: at least one skill is required")
    skills.update(qskills)

    knowledge = q.get("knowledge")
    if not isinstance(knowledge, list) or not knowledge:
        fail(f"{qid}: at least one knowledge reference is required")
    total_weight = 0.0
    for ref in knowledge:
        kid = ref.get("id")
        weight = ref.get("weight")
        if kid not in unit_ids:
            fail(f"{qid}: unknown knowledge unit {kid!r}")
        if not isinstance(weight, (int, float)) or weight <= 0 or weight > 1:
            fail(f"{qid}: invalid knowledge weight for {kid}")
        total_weight += float(weight)
    if total_weight > 1.000001:
        fail(f"{qid}: knowledge weights exceed 1.0")

    prerequisites = q.get("prerequisites")
    if not isinstance(prerequisites, list):
        fail(f"{qid}: prerequisites must be an array")
    if len(prerequisites) != len(set(prerequisites)):
        fail(f"{qid}: duplicate prerequisite ids")
    for prerequisite in prerequisites:
        if prerequisite not in unit_ids:
            fail(f"{qid}: unknown prerequisite knowledge unit {prerequisite!r}")

    prompt = q.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        fail(f"{qid}: prompt is empty")
    normalized_prompt = " ".join(prompt.lower().split())
    knowledge_key = tuple(ref.get("id") for ref in q.get("knowledge", []))
    duplicate_key = (normalized_prompt, knowledge_key)
    if duplicate_key in seen_prompts:
        fail(f"{qid}: duplicate prompt for same knowledge as {seen_prompts[duplicate_key]}")
    seen_prompts[duplicate_key] = qid

    options = q.get("options")
    if not isinstance(options, list) or len(options) < 2:
        fail(f"{qid}: at least two options are required")
    option_ids = [o.get("id") for o in options]
    if len(option_ids) != len(set(option_ids)):
        fail(f"{qid}: option ids must be unique")
    if any(not isinstance(o.get("text"), str) or not o["text"].strip() for o in options):
        fail(f"{qid}: option text is empty")

    answers = q.get("answer")
    if not isinstance(answers, list) or len(answers) != 1:
        fail(f"{qid}: single_choice needs exactly one answer")
    if answers[0] not in option_ids:
        fail(f"{qid}: answer {answers[0]!r} is not an option id")

    fb = q.get("feedback") or {}
    for field in ("short", "full", "rule"):
        value = fb.get(field)
        if isinstance(value, str):
            valid = bool(value.strip())
        elif isinstance(value, dict):
            valid = any(isinstance(text, str) and text.strip() for text in value.values())
        else:
            valid = False
        if not valid:
            fail(f"{qid}: feedback.{field} is required")

    review = q.get("review") or {}
    if review.get("status") != "published":
        fail(f"{qid}: only published questions may ship")

    if q.get("subject") != pack.get("subject"):
        fail(f"{qid}: subject {q.get('subject')!r} does not match pack subject {pack.get('subject')!r}")
    if q.get("grade_min", 0) < pack.get("grade_min", 0) or q.get("grade_max", 999) > pack.get("grade_max", 999):
        fail(f"{qid}: grade range falls outside pack range")

    stimulus = q.get("stimulus") or {}
    if q.get("mode") == "reading":
        if not stimulus.get("text"):
            fail(f"{qid}: reading requires stimulus.text")
        ev = q.get("evidence")
        if ev and ev.lower() not in stimulus["text"].lower():
            fail(f"{qid}: evidence is not present in stimulus.text")

    if q.get("mode") == "listening":
        listening += 1
        audio_path = stimulus.get("audio")
        script = stimulus.get("script")
        if not audio_path:
            fail(f"{qid}: listening requires stimulus.audio")
        if not script:
            fail(f"{qid}: listening requires stimulus.script")
        if audio_path in seen_audio_paths:
            fail(f"{qid}: audio path reused by {seen_audio_paths[audio_path]}")
        seen_audio_paths[audio_path] = qid

        pace = stimulus.get("pace", "normal")
        if pace not in {"slow", "normal"}:
            fail(f"{qid}: invalid listening pace {pace!r}")

        segments = stimulus.get("segments")
        if segments is not None:
            dialogues += 1
            if not isinstance(segments, list) or len(segments) < 2:
                fail(f"{qid}: dialogue requires at least two segments")
            segment_texts = []
            voices = set()
            for segment in segments:
                if segment.get("voice") not in {"lessac", "ryan"}:
                    fail(f"{qid}: unsupported segment voice {segment.get('voice')!r}")
                if not isinstance(segment.get("text"), str) or not segment["text"].strip():
                    fail(f"{qid}: empty dialogue segment")
                voices.add(segment["voice"])
                segment_texts.append(segment["text"])
            if len(voices) < 2:
                fail(f"{qid}: dialogue must use at least two voices")
            if " ".join(segment_texts).strip() != script.strip():
                fail(f"{qid}: dialogue segments must exactly reconstruct stimulus.script")
        else:
            if stimulus.get("voice") not in {"lessac", "ryan"}:
                fail(f"{qid}: monologue voice must be lessac or ryan")

        normalized_script = " ".join(script.lower().split())
        if normalized_script in seen_listening_scripts:
            fail(f"{qid}: duplicate listening script also used by {seen_listening_scripts[normalized_script]}")
        seen_listening_scripts[normalized_script] = qid

with DICTIONARY.open(encoding="utf-8") as f:
    dictionary = json.load(f)

entries = dictionary.get("entries")
if not isinstance(entries, list) or not entries:
    fail("dictionary entries must be a non-empty array")

lemmas = set()
forms = {}
for entry in entries:
    lemma = entry.get("lemma")
    if not isinstance(lemma, str) or not lemma.strip():
        fail("dictionary entry has no lemma")
    if lemma in lemmas:
        fail(f"dictionary duplicate lemma: {lemma}")
    lemmas.add(lemma)

    translation = entry.get("translation")
    definition = entry.get("definition")
    if not isinstance(translation, dict) or not translation:
        fail(f"dictionary {lemma}: translation map required")
    if not isinstance(definition, dict) or not definition:
        fail(f"dictionary {lemma}: definition map required")
    if not entry.get("example"):
        fail(f"dictionary {lemma}: example required")

    for form in entry.get("forms", []):
        normalized = form.lower().strip()
        if normalized in forms and forms[normalized] != lemma:
            fail(f"dictionary form {form!r} belongs to both {forms[normalized]} and {lemma}")
        forms[normalized] = lemma

with ECONOMY.open(encoding="utf-8") as f:
    economy = json.load(f)
reward_values = economy.get("rewards")
if not isinstance(reward_values, dict) or not reward_values:
    fail("economy rewards must be a non-empty object")
for key, value in reward_values.items():
    if not isinstance(value, int) or value < 0:
        fail(f"economy reward {key}: must be a non-negative integer")

with SHOP.open(encoding="utf-8") as f:
    shop = json.load(f)
shop_items = shop.get("items")
if not isinstance(shop_items, list) or len(shop_items) < 6:
    fail("shop must contain at least 6 items")
shop_skus = set()
allowed_shop_types = {"background", "button", "sound", "frame", "title", "reaction"}
for item in shop_items:
    sku = item.get("sku")
    if not isinstance(sku, str) or not sku:
        fail("shop item requires sku")
    if sku in shop_skus:
        fail(f"duplicate shop sku: {sku}")
    shop_skus.add(sku)
    if item.get("type") not in allowed_shop_types:
        fail(f"{sku}: unsupported shop type {item.get('type')!r}")
    price = item.get("price_crystals")
    if not isinstance(price, int) or price < 0:
        fail(f"{sku}: price must be a non-negative integer")
    if not isinstance(item.get("name"), dict) or not item["name"]:
        fail(f"{sku}: localized name required")
    if not isinstance(item.get("payload"), dict):
        fail(f"{sku}: payload object required")

with REWARDS.open(encoding="utf-8") as f:
    reward_catalog = json.load(f)
digital_items = reward_catalog.get("items")
if not isinstance(digital_items, list) or not digital_items:
    fail("digital reward catalog must contain items")
digital_skus = set()
for item in digital_items:
    sku = item.get("sku")
    if not isinstance(sku, str) or not sku:
        fail("digital reward requires sku")
    if sku in digital_skus or sku in shop_skus:
        fail(f"duplicate reward sku: {sku}")
    digital_skus.add(sku)
    price = item.get("price_crystals")
    if not isinstance(price, int) or price < 0:
        fail(f"{sku}: price must be a non-negative integer")
    rights = item.get("rights") or {}
    fulfillment = item.get("fulfillment") or {}
    if item.get("enabled"):
        if item.get("backend_required"):
            fail(f"{sku}: backend-required external reward must remain disabled in offline MVP")
        if rights.get("status") != "owned_original":
            fail(f"{sku}: enabled offline reward must be owned_original")
        if fulfillment.get("mode") != "asset":
            fail(f"{sku}: enabled offline reward must use asset fulfillment")
        asset = fulfillment.get("asset")
        if not isinstance(asset, str) or not asset:
            fail(f"{sku}: enabled asset reward needs asset path")
        if not (ROOT / "app/src/main/assets" / asset).exists():
            fail(f"{sku}: reward asset not found: {asset}")

with MINIGAMES.open(encoding="utf-8") as f:
    minigames = json.load(f)
interval = minigames.get("break_interval_questions")
if not isinstance(interval, int) or interval < 1:
    fail("mini-game break interval must be >= 1")
strategy = minigames.get("selection_strategy", "round_robin")
if strategy not in {"round_robin"}:
    fail(f"unsupported mini-game selection strategy: {strategy!r}")
games = minigames.get("games")
if not isinstance(games, list) or not games:
    fail("mini-game config needs at least one game")
game_ids = set()
for game in games:
    gid = game.get("id")
    if not isinstance(gid, str) or not gid:
        fail("mini-game id is required")
    if gid in game_ids:
        fail(f"duplicate mini-game id: {gid}")
    game_ids.add(gid)
    duration = game.get("duration_seconds")
    if not isinstance(duration, int) or not 5 <= duration <= 60:
        fail(f"{gid}: duration must be 5..60 seconds")
    for field in ("completion_reward", "score_bonus_every", "score_bonus_cap"):
        value = game.get(field)
        if not isinstance(value, int) or value < 0:
            fail(f"{gid}: {field} must be non-negative integer")
if minigames.get("default_game") not in game_ids:
    fail("default mini-game must exist in games")
enabled_games = {g.get("id") for g in games if g.get("enabled")}
if len(enabled_games) < 3:
    fail("v0.6 requires at least three enabled break games")
for required_game in {"match3", "memory", "tap_spark"}:
    if required_game not in enabled_games:
        fail(f"required v0.6 mini-game is disabled/missing: {required_game}")

with CATALOG.open(encoding="utf-8") as f:
    catalog = json.load(f)
catalog_pack_list = catalog.get("packs", [])
if not isinstance(catalog_pack_list, list) or not catalog_pack_list:
    fail("catalog packs must be a non-empty array")

global_unit_ids = set()
loaded_pack_banks = {}
for catalog_pack in catalog_pack_list:
    asset = catalog_pack.get("asset")
    path = ROOT / "app/src/main/assets" / str(asset)
    if not path.exists():
        fail(f"catalog pack asset not found: {asset}")
    with path.open(encoding="utf-8") as f:
        candidate_bank = json.load(f)
    loaded_pack_banks[catalog_pack.get("id")] = candidate_bank
    candidate_pack = candidate_bank.get("pack") or {}
    if candidate_pack.get("id") != catalog_pack.get("id"):
        fail(f"catalog/bank id mismatch for {catalog_pack.get('id')}")
    if candidate_pack.get("subject") != catalog_pack.get("subject"):
        fail(f"catalog/bank subject mismatch for {catalog_pack.get('id')}")
    for unit in candidate_bank.get("knowledge_units", []):
        uid = unit.get("id")
        if uid in global_unit_ids:
            fail(f"knowledge unit must be globally unique across packs: {uid}")
        global_unit_ids.add(uid)
    candidate_ids = {u.get("id") for u in candidate_bank.get("knowledge_units", [])}
    candidate_questions = candidate_bank.get("questions")
    if not isinstance(candidate_questions, list) or not candidate_questions:
        fail(f"{catalog_pack.get('id')}: questions must be non-empty")
    for question in candidate_questions:
        qid = question.get("id")
        if question.get("subject") != candidate_pack.get("subject"):
            fail(f"{qid}: subject does not match its pack")
        if question.get("interaction") != "single_choice":
            fail(f"{qid}: runtime currently supports single_choice")
        if (question.get("review") or {}).get("status") != "published":
            fail(f"{qid}: only published questions may ship")
        for ref in question.get("knowledge", []):
            if ref.get("id") not in candidate_ids:
                fail(f"{qid}: assessed knowledge is outside its pack: {ref.get('id')}")
        for prerequisite in question.get("prerequisites", []):
            if prerequisite not in global_unit_ids and prerequisite not in candidate_ids:
                fail(f"{qid}: unknown prerequisite {prerequisite}")

with ATLAS.open(encoding="utf-8") as f:
    atlas = json.load(f)

allowed_relations = {
    "requires", "uses", "is_part_of", "generalizes", "specializes",
    "equivalent_to", "often_confused_with", "applied_in", "assessed_by"
}
relations = atlas.get("relations")
if not isinstance(relations, list):
    fail("knowledge atlas relations must be an array")

requires_graph = {uid: [] for uid in global_unit_ids}
seen_relations = set()
for relation in relations:
    src = relation.get("from")
    rel_type = relation.get("type")
    dst = relation.get("to")
    if src not in global_unit_ids or dst not in global_unit_ids:
        fail(f"knowledge atlas relation references unknown unit: {src!r} -> {dst!r}")
    if rel_type not in allowed_relations:
        fail(f"unsupported knowledge relation type: {rel_type!r}")
    key = (src, rel_type, dst)
    if key in seen_relations:
        fail(f"duplicate knowledge relation: {key}")
    seen_relations.add(key)
    if rel_type == "requires":
        requires_graph[src].append(dst)

visiting = set()
done = set()
def visit_requires(node):
    if node in done:
        return
    if node in visiting:
        fail(f"requires cycle detected at {node}")
    visiting.add(node)
    for nxt in requires_graph.get(node, []):
        visit_requires(nxt)
    visiting.remove(node)
    done.add(node)

for uid in global_unit_ids:
    visit_requires(uid)

with PLAY_CREDITS.open(encoding="utf-8") as f:
    play_credits = json.load(f)
for field in ("questions_per_credit", "max_balance", "game_session_cost"):
    value = play_credits.get(field)
    if not isinstance(value, int) or value < 1:
        fail(f"play_credits.{field} must be a positive integer")
if play_credits["game_session_cost"] > play_credits["max_balance"]:
    fail("game_session_cost cannot exceed max_balance")

default_pack = catalog.get("default_pack")
catalog_packs = {p.get("id"): p for p in catalog.get("packs", [])}
if default_pack not in catalog_packs:
    fail("catalog default_pack is missing")

with ENTITLEMENTS.open(encoding="utf-8") as f:
    entitlement_catalog = json.load(f)
grants = entitlement_catalog.get("grants")
if not isinstance(grants, list) or not grants:
    fail("entitlements.grants must be non-empty")
accessible_pack_ids = set()
for grant in grants:
    if not grant.get("active"):
        continue
    pack_ids = grant.get("pack_ids", [])
    if not isinstance(pack_ids, list):
        fail(f"entitlement {grant.get('id')}: pack_ids must be an array")
    accessible_pack_ids.update(pack_ids)
for pack_id, catalog_pack in catalog_packs.items():
    if catalog_pack.get("enabled") and pack_id not in accessible_pack_ids:
        fail(f"enabled pack has no active entitlement grant: {pack_id}")

with LICENSES.open(encoding="utf-8") as f:
    license_manifest = json.load(f)
license_rows = license_manifest.get("licenses")
if not isinstance(license_rows, list) or not license_rows:
    fail("license manifest must be non-empty")
licenses = {row.get("id"): row for row in license_rows}
allowed_rights = {"owned_original", "licensed", "public_domain", "open_license"}
for license_id, row in licenses.items():
    if row.get("rights_type") not in allowed_rights:
        fail(f"license {license_id}: unsupported or unverified rights type")
    if not row.get("active") or not row.get("distribution_allowed"):
        fail(f"license {license_id}: inactive or non-distributable")
    if not isinstance(row.get("territories"), list) or not row.get("territories"):
        fail(f"license {license_id}: territories are required")
for pack_id, catalog_pack in catalog_packs.items():
    if catalog_pack.get("enabled") and catalog_pack.get("license_id") not in licenses:
        fail(f"enabled pack has no verified license: {pack_id}")

with PRODUCTS.open(encoding="utf-8") as f:
    product_catalog = json.load(f)
allowed_providers = {"pilot", "google_play", "app_store", "ru_cis", "promo"}
if set(product_catalog.get("providers", [])) != allowed_providers:
    fail("product provider registry must explicitly contain all supported adapters")
product_ids = set()
for product in product_catalog.get("products", []):
    product_id = product.get("id")
    if not product_id or product_id in product_ids:
        fail(f"invalid or duplicate product id: {product_id}")
    product_ids.add(product_id)
    if product.get("provider") not in allowed_providers:
        fail(f"{product_id}: unsupported provider")
    if product.get("checkout_enabled"):
        fail(f"{product_id}: real checkout must remain disabled in the pilot")
    scope = product.get("scope") or {}
    for pack_id in scope.get("pack_ids", []):
        if pack_id not in catalog_packs:
            fail(f"{product_id}: unknown pack in scope: {pack_id}")

with TARGETS.open(encoding="utf-8") as f:
    targets_catalog = json.load(f)
targets = targets_catalog.get("targets")
if not isinstance(targets, list) or not targets:
    fail("training targets must be non-empty")
targets_by_pack = {target.get("pack_id"): target for target in targets}
for pack_id, catalog_pack in catalog_packs.items():
    if not catalog_pack.get("enabled"):
        continue
    target = targets_by_pack.get(pack_id)
    if target is None:
        fail(f"enabled pack needs a training target: {pack_id}")
    target_date = target.get("target_date")
    if not isinstance(target_date, str) or len(target_date.split("-")) != 3:
        fail(f"{pack_id}: training target date must be YYYY-MM-DD")
    if target.get("mode") not in {"competition", "general"}:
        fail(f"{pack_id}: training target mode must be competition/general")

print(
    f"OK: pack={pack['id']}, {len(questions)} questions, {len(unit_ids)} knowledge units, "
    f"{len(catalog_packs)} packs, {len(global_unit_ids)} global knowledge units, "
    f"{len(relations)} atlas relations, {len(skills)} tags, "
    f"{listening} listening items ({dialogues} dialogues), "
    f"{len(entries)} dictionary entries, {len(shop_items)} shop items, "
    f"{len(digital_items)} digital rewards, {len(games)} mini-games, "
    f"{len(grants)} entitlement grants, {len(product_ids)} products, {len(licenses)} licenses"
)
