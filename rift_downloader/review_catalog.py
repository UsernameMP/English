"""Non-destructive review catalog for existing RIFT original documents.

Labels come strictly from URLs and filenames, NOT PDF content. Keep this
provenance catalog separate from the content-verification pipeline. Does not
download anything or modify the original documents.
"""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse,unquote

FIELDS=('resource_id','original_filename','url','source_url','mime_type',
        'size_bytes','object_sha256','drive_file_id','suggested_group',
        'rule_signal','review_priority','review_status','classification_basis')

RULES=(
    ('likely_unrelated','high',
     r'(?<![a-z])(catalog(?:ue)?|databook|campus|site.?map|ynu.?map|map|privacy|terms.?of.?use|staff.?directory)(?![a-z])'),
    ('results_or_rankings','high',
     r'(?<![a-z])(results?|rezultate|rezultat|ranking|rankings|classific|winner|winners|medals?|scores?)(?![a-z])'),
    ('grading_and_criteria','medium',
     r'(?<![a-z])(criteria|criteri|kriteri|marking|rubric|grading|markscheme|answer.?key)(?![a-z])'),
    ('solutions_and_answers','medium',
     r'(?<![a-z])(solutions?|solu(?:ti|c)|answer|answers|resen|resheni|worked.?out)(?![a-z])'),
    ('problem_or_task_candidate','low',
     r'(?<![a-z])(problems?|task|tasks|problemset|contest.?problems?|zadac|zadaci|zadat|prueb|exam|examen|question|questions|olimpiad.*zad)(?![a-z])')
)
REVIEW_DEFAULT=('uncertain','high','no file-name signal')
REVIEW_STATUS='pending_content_review'
BASIS='URL and filename heuristic only; not a content-based or validated classification'

def _tokens(url):
    parts=urlparse(url)
    name=unquote(parts.path.rsplit('/',1)[-1]) or '[no-filename]'
    # Include complete path but not source hostname to reduce accidental
    # 'results' detection on a site whose name itself includes the word.
    path=unquote(parts.path).lower()
    text=re.sub(r'[_/.\-+]+',' ',path)
    return name,text

def classify(url,source_url=''):
    filename,path=_tokens(url)
    # Path is primary evidence; source parent page only helps when the file
    # endpoint has no recognizable category signal.
    for group,priority,pattern in RULES:
        match=re.search(pattern,path,re.I)
        if match:
            return group,match.group(0),priority
    source_path=unquote(urlparse(source_url).path).lower()
    if re.search(r'(olymp|contest|competition|tasks?|problems?|zadaci|archive)',source_path):
        return 'source_context_candidate','olympiad/contest-like source page','medium'
    return REVIEW_DEFAULT[0],REVIEW_DEFAULT[2],REVIEW_DEFAULT[1]

def _csv_safe(value):
    val='' if value is None else str(value)
    if val.lstrip().startswith(('=','+','-','@','\t','\r')):
        return "'"+val
    return val

def review_rows(rows):
    seen=set()
    for item in rows:
        rid=item.get('resource_id','')
        sha=item.get('object_sha256','')
        if not rid or not sha or sha in seen:
            continue
        seen.add(sha)
        filename,_=_tokens(item.get('url',''))
        group,signal,priority=classify(item.get('url',''),item.get('source_url',''))
        yield {
            'resource_id':rid,'original_filename':filename,
            'url':item.get('url',''),'source_url':item.get('source_url',''),
            'mime_type':item.get('mime_type',''),
            'size_bytes':item.get('size_bytes',''),
            'object_sha256':sha,'drive_file_id':item.get('drive_file_id',''),
            'suggested_group':group,'rule_signal':signal,
            'review_priority':priority,'review_status':REVIEW_STATUS,
            'classification_basis':BASIS
        }

def catalog(manifest_path,output_path):
    with open(manifest_path,encoding='utf-8',newline='') as handle:
        rows=list(review_rows(csv.DictReader(handle)))
    out=Path(output_path)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key:_csv_safe(row.get(key)) for key in FIELDS})
    return {'rows':len(rows),'by_group':dict(sorted(Counter(r['suggested_group'] for r in rows).items())),
            'review_priority':dict(sorted(Counter(r['review_priority'] for r in rows).items())),
            'output':str(out)}

def main():
    parser=argparse.ArgumentParser(description='Offline RIFT 200-file review catalog; NO downloads')
    parser.add_argument('--manifest',required=True,help='Existing pilot_report_manifest.csv')
    parser.add_argument('--output',required=True,help='Catalog CSV to create')
    args=parser.parse_args()
    import json
    print(json.dumps(catalog(args.manifest,args.output),ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
