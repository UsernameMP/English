#!/usr/bin/env python3
"""Deterministic answer-key checks for the grade-5 2026/27 AI task pack."""
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1] / "app/src/main/assets/content/informatics_g5_school_2026_ai.json"
data = json.loads(BANK.read_text(encoding="utf-8"))
questions = {q["id"].removeprefix("cs5_school2627_ai_"): q for q in data["questions"]}
assert len(questions) == 18, "expected 18 independently graded items"

def chosen(question):
    if question["interaction"] == "numeric":
        return question["answer"][0]
    answer_id = question["answer"][0]
    return next(o["text"] for o in question["options"] if o["id"] == answer_id)

def expect(key, answer):
    actual = chosen(questions[key])
    assert actual == str(answer), f"{key}: {actual!r}, expected {answer!r}"

# Exactly two of three models succeed on each of 100 requests.
expect("votes_01", 100 * 2 - 67 - 85)

# Reverse-operation uniqueness for all possible predecessors of a number.
def transform(n):
    return n + 12 if n % 6 == 0 else n - 5 if n % 2 == 1 else n + 8

possible = set()
for initial in range(1, 101):
    current = initial
    for steps in range(1, 10):
        current = transform(current)
        if current == 70 and steps >= 2:
            possible.add(initial)
assert possible == {67}, possible
expect("reverse_01", 67)

# Lower bound and explicit attaining construction on an odd cycle.
lights = "11100" * 42 + "1"
assert len(lights) == 211 and lights.count("1") == 127
assert 126 * 5 < 211 * 3 <= 127 * 5
for i in range(211):
    assert sum(lights[(i + j) % 211] == "1" for j in range(5)) >= 3
expect("ring_01", 127)

# Reconstruct distances on the original 5x5 monochrome patterns.
three = ["11110", "00010", "01110", "00010", "11110"]
eight = ["01110", "10001", "01110", "10001", "01110"]
patterns = {
    "a": ["11110", "00010", "01010", "00010", "11110"],
    "b": ["01110", "10001", "01010", "10001", "01110"],
    "c": ["11110", "00010", "01010", "00001", "01110"],
    "d": ["01110", "00010", "01010", "00001", "01110"],
}
def distance(x, y):
    return sum(a != b for row_x, row_y in zip(x, y) for a, b in zip(row_x, row_y))
for name, bits in patterns.items():
    d3, d8 = distance(bits, three), distance(bits, eight)
    prediction = 3 if d3 < d8 else 8
    expect(f"pixels_{name}", f"{d3} / {d8} / {prediction}")
    q = questions[f"pixels_{name}"]
    assert "Изображение " + name.upper() + ":\\n" + "\\n".join(bits) in q["stimulus"]["text"]

# Edit distances and leftmost tie breaking for the corrected dictionary.
words = ["кот", "кит", "рот", "код"]
for i, source in enumerate(["кат", "род", "код"], start=1):
    distances = [sum(a != b for a, b in zip(source, target)) for target in words]
    expect(f"words_dist_{i}", ", ".join(map(str, distances)))
    expect(f"words_fix_{i}", words[distances.index(min(distances))])
expect("words_edit_01", "кад")
alphabet = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
assert len(alphabet) == 33
winning_edits = []
for position in range(3):
    for letter in alphabet:
        if letter == "кат"[position]:
            continue
        variant = "кат"[:position] + letter + "кат"[position + 1:]
        distances = [sum(a != b for a, b in zip(variant, target)) for target in words]
        if distances.index(min(distances)) == 3:
            winning_edits.append(variant)
assert winning_edits == ["кад"], winning_edits
expect("words_count_01", len(winning_edits))

# ceil-halving and binary-merging capacity.
size = 17
for _ in range(2):
    size = (size + 1) // 2
expect("tokens_01", size)
size, steps = 17, 0
while size > 1:
    size = (size + 1) // 2
    steps += 1
expect("tokens_02", steps)
expect("tokens_03", 2 ** 6 + 1)
print("OK: 6 source tasks, 18 exercises, image grids, tie breaks and boundary cases")
