#!/usr/bin/env python3
"""Conservative, multilingual URL hints. Never discards link evidence."""
import hashlib
import re
from urllib.parse import urlparse, urldefrag

FILE_EXTS = (".pdf", ".doc", ".docx", ".zip", ".rar", ".7z", ".djvu",
             ".tex", ".ps", ".xls", ".xlsx", ".ppt", ".pptx", ".torrent")
MEDIA_HINTS = ("/pdf/", "/media-download/", "/file/download/", "/download/")
# Words are only contextual evidence, NEVER proof that a document is a problem.
# Rules deliberately cover original languages of currently indexed archives.
VOCAB = {
    "task": (
        "problem", "problems", "question", "questions", "exam", "exams", "paper",
        "aufgabe", "aufgaben", "angabe", "aufgabenstellung", "sujet", "énoncé",
        "enonce", "problème", "probleme", "zadani", "zadání", "zadania", "zadania",
        "zadaci", "zadatak", "zadatci", "zadatak", "prova", "provas", "prueba",
        "pruebas", "problemas", "problema", "soal", "soalan", "soru", "sorular",
        "sınav", "sinav", "予選", "本選", "問題", "試題", "试题", "問題集",
        "문제", "задания", "задани", "задачи", "вопросы", "масъала",
    ),
    "solution": (
        "solutions", "solution", "soluzioni", "soluzione", "lösung", "lösungen",
        "losung", "losungen", "corrigé", "corrige", "correction", "resolução",
        "resoluções", "resolucao", "resoluciones", "soluciones", "gabarito",
        "gabaritos", "cevapları", "cevaplar", "cevap", "jawaban", "pembahasan",
        "解答", "解説", "答案", "풀이", "해설", "ответы", "ответ", "решения",
        "решение", "розв'язки", "розв’язки", "rješenja", "resenja", "řešení",
    ),
    "criteria": (
        "marking", "markscheme", "mark scheme", "rubric", "grading",
        "scoring scheme", "scheme of evaluation", "bewertung",
        "bewertungsrichtlinie", "barème", "bareme", "kriterien",
        "évaluation", "criterios", "critérios", "pontuação",
        "puanj", "puanlama", "评分", "採点", "配点", "критерии",
        "оценивания", "баллы",
    ),
    "archive": (
        "archive", "archives", "past papers", "past problems", "archiv",
        "archivio", "archivum", "archiwum", "archiwalne", "archief",
        "archivo", "arquivos", "historique", "annales", "geçmiş",
        "yılları", "历年", "過去問", "過去", "архив", "өткен",
    ),
}
NAVIGATION = (
    "privacy", "impressum", "contact", "kontakt", "datenschutz",
    "about us", "membership", "member", "registration", "login",
    "news", "newsletter", "donate", "cookies", "support", "sponsor",
    "datenschutzerklärung", "inscription", "inscripción", "datenschutz",
    "политика конфиденциальности", "контакты", "о нас",
)


def canonical_resource_url(url):
    """Canonical identity, preserving meaningful query parameters and case-sensitive path."""
    url = urldefrag(url.strip())[0]
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return ""
    # Do not strip www, trailing slash, query, or percent-encoded bytes:
    # these can distinguish actual archive documents.
    return parsed._replace(scheme=parsed.scheme.lower(),
                           netloc=parsed.netloc.lower()).geturl()


def resource_id(url):
    clean = canonical_resource_url(url)
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:24] if clean else ""


def likely_file(url, mime=""):
    path = urlparse(url).path.lower()
    m = mime.lower().split(";", 1)[0].strip()
    return (path.endswith(FILE_EXTS) or any(x in path for x in MEDIA_HINTS)
            or m in ("application/pdf", "application/zip", "application/x-zip-compressed",
                     "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     "application/x-7z-compressed", "application/x-rar-compressed",
                     "application/x-bittorrent"))


def hint(url, anchor="", title="", heading="", mime=""):
    """Weak multilingual classification hint and crawl priority; no automatic rejection."""
    path = urlparse(url).path.lower()
    # The parent heading supplies document-year context but should not classify
    # an 'About' menu item as a problem just because the page is an archive.
    primary = " ".join((anchor, title, path)).lower()
    contextual = (heading or "").lower()
    matches = {}
    for category, terms in VOCAB.items():
        found = [t for t in terms if (t in primary or (likely_file(url, mime) and t in contextual))]
        if found:
            matches[category] = found[:3]
    if len(set(matches) & {"task", "solution", "criteria"}) > 1:
        kind = "review"  # mixed problems+answers, or ambiguous label
    elif "criteria" in matches:
        kind = "criteria"
    elif "solution" in matches:
        kind = "solution"
    elif "task" in matches:
        kind = "task"
    elif "archive" in matches:
        kind = "archive"
    else:
        kind = "review"
    nav = any(t in primary for t in NAVIGATION)
    file_candidate = likely_file(url, mime)
    # High priority for archive index pages, linked documents; low priority for
    # navigation. ALL links remain in raw evidence and HTML frontier.
    if file_candidate:
        priority = 3
    elif nav:
        priority = 0
    elif kind in ("task", "solution", "criteria", "archive"):
        priority = 2
    else:
        priority = 1
    return {"type_hint": kind, "priority": priority, "file_candidate": file_candidate,
            "hint_evidence": {k: v for k, v in matches.items()},
            "needs_review": True}  # hints are not verified semantic labels
