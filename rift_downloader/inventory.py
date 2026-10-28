"""Zero-network inventory of already-discovered resource URLs.

Predictions use existing source MIME evidence and URL suffixes, not a new
request to the site. They are estimates, not a claim about actual file types.
"""
from collections import Counter
from pathlib import PurePosixPath
from urllib.parse import unquote,urlparse

SUFFIX_GROUP={
    '.pdf':'pdf',
    '.doc':'word','.docx':'word','.odt':'word','.rtf':'word',
    '.zip':'archive','.rar':'archive','.7z':'archive','.tar':'archive',
    '.gz':'archive','.tgz':'archive','.bz2':'archive','.xz':'archive',
    '.ppt':'presentation','.pptx':'presentation','.odp':'presentation',
    '.xls':'spreadsheet','.xlsx':'spreadsheet','.ods':'spreadsheet','.csv':'spreadsheet',
    '.tex':'other_document','.ps':'other_document','.epub':'other_document'
}
MIME_GROUP={
    'application/pdf':'pdf',
    'application/msword':'word',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document':'word',
    'application/vnd.oasis.opendocument.text':'word',
    'application/zip':'archive',
    'application/x-zip-compressed':'archive',
    'application/x-rar-compressed':'archive',
    'application/x-7z-compressed':'archive',
    'application/vnd.ms-powerpoint':'presentation',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation':'presentation',
    'application/vnd.ms-excel':'spreadsheet',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':'spreadsheet',
    'application/vnd.oasis.opendocument.spreadsheet':'spreadsheet',
    'application/x-tex':'other_document'
}
def predicted_type(url,mime):
    mime=(mime or '').split(';',1)[0].strip().lower()
    if mime in MIME_GROUP:return MIME_GROUP[mime]
    ext=PurePosixPath(unquote(urlparse(url).path)).suffix.lower()
    if ext in SUFFIX_GROUP:return SUFFIX_GROUP[ext]
    if ext in ('.html','.htm','.php','.asp','.aspx') or mime in ('text/html','application/xhtml+xml'):
        return 'html_likely'
    return 'unknown'

def inventory(db,sample=12):
    n=Counter();known=Counter();hosts=Counter();candidate_hosts=Counter()
    first=[]
    for row in db.execute('SELECT resource_id,url,mime_hint,file_candidate FROM resources ORDER BY resource_id'):
        url=row['url'];flag=bool(row['file_candidate'])
        group=predicted_type(url,row['mime_hint'])
        n[group]+=1
        if row['mime_hint']:known[group]+=1
        host=urlparse(url).hostname or 'unknown'
        hosts[host]+=1
        if flag or group in ('pdf','word','archive','presentation','spreadsheet','other_document'):
            candidate_hosts[host]+=1
            if len(first)<sample:
                first.append({'resource_id':row['resource_id'],'url':url,'predicted_type':group,
                              'file_candidate':flag,'mime_hint':row['mime_hint']})
    file_types=('pdf','word','archive','presentation','spreadsheet','other_document')
    return {
        'warning':'Offline estimate from URLs and previously observed MIME; actual types must be checked during download.',
        'total_urls':sum(n.values()),
        'estimated_file_urls':sum(n[k] for k in file_types),
        'prior_flagged_file_candidates':db.execute('SELECT COUNT(*) FROM resources WHERE file_candidate=1').fetchone()[0],
        'by_prediction':dict(sorted(n.items())),
        'with_prior_mime_evidence':dict(sorted(known.items())),
        'total_hosts':len(hosts),
        'candidate_hosts':len(candidate_hosts),
        'top_candidate_hosts':candidate_hosts.most_common(15),
        'sample_candidate_urls':first
    }
