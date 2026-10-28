"""Polite streaming HTTP worker; never fetches HTML bodies or private addresses."""
import email.utils
import hashlib
import ipaddress
import os
import random
import socket
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse,unquote
from urllib.robotparser import RobotFileParser
import requests

EXTENSIONS={'.pdf','.doc','.docx','.zip','.rar','.7z','.tar','.gz','.tgz',
            '.ppt','.pptx','.xls','.xlsx','.ods','.odt','.rtf','.tex','.ps','.epub'}
MIMES={'application/pdf','application/zip','application/x-zip-compressed',
       'application/x-rar-compressed','application/vnd.rar','application/x-7z-compressed',
       'application/x-tar','application/gzip','application/msword',
       'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
       'application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
       'application/vnd.ms-powerpoint',
       'application/vnd.openxmlformats-officedocument.presentationml.presentation',
       'application/vnd.oasis.opendocument.text','application/vnd.oasis.opendocument.spreadsheet',
       'application/rtf','application/postscript','application/epub+zip','application/x-tex'}
USER_AGENT='RIFT-ResearchArchive/0.1 (polite pilot; respects robots and Retry-After)'

class UnsafeURL(ValueError):pass
class RobotsDenied(ValueError):pass
class RobotsRetry(RuntimeError):
    def __init__(self,status,delay=None):
        self.status=status
        self.delay=delay
        super().__init__(f'robots.txt returned HTTP {status}')

def safe_url(url,resolve=True):
    parts=urlparse(url)
    if parts.scheme not in ('http','https') or not parts.hostname or parts.username or parts.password:
        raise UnsafeURL('unsupported URL scheme/credentials')
    host=parts.hostname.lower().rstrip('.')
    if host=='localhost' or host.endswith(('.localhost','.local','.internal')):
        raise UnsafeURL('local hostname')
    try:
        if parts.port is not None and parts.port not in (80,443):
            raise UnsafeURL('non-standard port blocked in pilot')
    except ValueError as exc:
        raise UnsafeURL('invalid port') from exc
    try:
        ip=ipaddress.ip_address(host.strip('[]'))
    except ValueError:
        ip=None
    if ip is not None:
        if not ip.is_global:raise UnsafeURL('non-public address')
    else:
        if resolve:
            addresses=socket.getaddrinfo(host,parts.port or (443 if parts.scheme=='https' else 80),type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(addr[4][0]).is_global for addr in addresses):
                raise UnsafeURL('DNS includes non-public address')
    return host

class RateLimiter:
    """Conservative per-host pacing, persisted to SQLite across process restarts.

    A host cooldown is set *before* each request; if the process crashes during
    a request, a restarted worker still waits. Caller must own a singleton lock.
    """
    def __init__(self,delay=10.0,clock=time.monotonic,sleep=time.sleep,
                 state=None,wall_clock=time.time):
        self.delay=float(delay)
        self.clock=clock
        self.sleep=sleep
        self.wall_clock=wall_clock
        self.state=state
        self.next_at={}
        self.last_at={}
        self.last_wall={}
    def _saved(self,host):
        if self.state is None:return (0.,0.)
        row=self.state.execute(
            'SELECT last_request_at,next_allowed_at FROM host_pacing WHERE host=?',
            (host,)).fetchone()
        return (float(row[0]),float(row[1])) if row else (0.,0.)
    def _write(self,host,previous,next_allowed):
        if self.state is not None:
            with self.state:
                self.state.execute('''INSERT INTO host_pacing
                    (host,last_request_at,next_allowed_at,last_updated_at)
                    VALUES (?,?,?,?)
                    ON CONFLICT(host) DO UPDATE SET
                    last_request_at=MAX(host_pacing.last_request_at,excluded.last_request_at),
                    next_allowed_at=MAX(host_pacing.next_allowed_at,excluded.next_allowed_at),
                    last_updated_at=excluded.last_updated_at''',
                    (host,previous,next_allowed,self.wall_clock()))
    def wait(self,host,minimum=None):
        interval=max(self.delay,float(minimum or 0))
        now=self.clock()
        wall=self.wall_clock()
        last_saved,next_saved=self._saved(host)
        last=max(self.last_wall.get(host,0),last_saved)
        wait=max(0.,self.next_at.get(host,0)-now,
                 next_saved-wall,
                 last+interval-wall if last else 0.)
        if wait:self.sleep(wait)
        now=self.clock()
        wall=self.wall_clock()
        self.next_at[host]=now+interval
        self.last_at[host]=now
        self.last_wall[host]=wall
        self._write(host,wall,wall+interval)
        return int(round(wait*1000))
    def postpone(self,host,seconds):
        seconds=max(0.,float(seconds))
        deadline=self.clock()+seconds
        self.next_at[host]=max(self.next_at.get(host,0.),deadline)
        if self.state is not None:
            previous,next_saved=self._saved(host)
            wall_deadline=max(next_saved,self.wall_clock()+seconds)
            self._write(host,previous,wall_deadline)

def retry_after(header):
    if not header:return None
    try:return max(0,float(header))
    except ValueError:
        try:
            dt=email.utils.parsedate_to_datetime(header)
            if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
            return max(0,(dt-datetime.now(timezone.utc)).total_seconds())
        except (TypeError,ValueError,OverflowError):return None

def kind(mime,url,prefix):
    mime=(mime or '').split(';')[0].strip().lower()
    ext=Path(unquote(urlparse(url).path)).suffix.lower()
    first=prefix[:256].lstrip().lower()
    # Images belong to a later HTML/visual-asset archival stage, not this pilot.
    # Magic signatures take precedence over misleading server MIME headers.
    if (prefix.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff',
                           b'GIF87a',b'GIF89a',b'RIFF')) and
        not prefix.startswith(b'Rar!')):
        return 'image',mime
    if mime.startswith('image/') or Path(unquote(urlparse(url).path)).suffix.lower() in (
        '.png','.jpg','.jpeg','.gif','.webp','.svg','.bmp','.tiff','.tif'):
        return 'image',mime
    if first.startswith((b'<!doctype html',b'<html',b'<?xml')) and b'<html' in first[:256]:
        return 'html',mime
    # A recognizable file signature overrides misleading HTML Content-Type or URL suffix.
    if prefix.startswith(b'%PDF-'):return 'file','application/pdf'
    if prefix.startswith(b'PK\x03\x04'):
        office={'.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.ods':'application/vnd.oasis.opendocument.spreadsheet',
                '.odt':'application/vnd.oasis.opendocument.text',
                '.epub':'application/epub+zip'}
        if mime in MIMES and mime not in ('application/zip','application/x-zip-compressed'):
            return 'file',mime
        return 'file',office.get(ext,mime if mime in MIMES else 'application/zip')
    if mime in ('text/html','application/xhtml+xml') or ext in ('.html','.htm'):
        return 'html',mime
    if prefix.startswith(b'Rar!\x1a\x07'):return 'file','application/vnd.rar'
    if prefix.startswith(b'7z\xbc\xaf\x27\x1c'):return 'file','application/x-7z-compressed'
    if prefix.startswith(b'\x1f\x8b'):return 'file','application/gzip'
    if prefix.startswith(b'\xd0\xcf\x11\xe0'):return 'file',mime if mime in MIMES else 'application/msword'
    if mime in MIMES:return 'file',mime
    if ext in EXTENSIONS:return 'file',mime or 'application/octet-stream'
    return 'other',mime

class PoliteHttp:
    def __init__(self,delay=10,timeout=30,max_bytes=100*1024*1024,session=None,limiter=None,dns_check=True,on_response=None):
        self.session=session or requests.Session()
        self.session.trust_env=False
        self.session.headers.update({'User-Agent':USER_AGENT,'Accept':'*/*',
                                     'Accept-Encoding':'identity'})
        self.limiter=limiter or RateLimiter(delay)
        self.timeout=timeout
        self.max_bytes=max_bytes
        self.dns_check=dns_check
        self.on_response=on_response
        self.robots_cache={}
    def _request(self,url,*,minimum=None,purpose='resource'):
        host=safe_url(url,self.dns_check)
        waited=self.limiter.wait(host,minimum=minimum)
        started=time.monotonic()
        response=self.session.get(url,stream=True,timeout=(10,self.timeout),allow_redirects=False)
        elapsed=int((time.monotonic()-started)*1000)
        if self.on_response is not None:
            self.on_response(url,host,purpose,response.status_code,elapsed,waited)
        return response,waited
    def _robots(self,url):
        parts=urlparse(url)
        origin=f'{parts.scheme}://{parts.netloc}'
        if origin in self.robots_cache:return self.robots_cache[origin]
        target=origin+'/robots.txt'
        for _ in range(4):
            response,wait=self._request(target,purpose='robots')
            with response:
                code=response.status_code
                if code in (301,302,303,307,308):
                    location=response.headers.get('Location')
                    if not location:raise RobotsDenied('robots redirect missing location')
                    target=urljoin(target,location)
                    continue
                if code in (404,410):
                    value=(None,0)
                elif code in (429,500,502,503,504):
                    raise RobotsRetry(code,retry_after(response.headers.get('Retry-After')))
                elif code!=200:
                    raise RobotsDenied(f'robots.txt unavailable HTTP {code} (fail closed)')
                else:
                    body=b''
                    for chunk in response.iter_content(8192):
                        body+=chunk
                        if len(body)>1024*1024:raise RobotsDenied('robots.txt too large')
                    parser=RobotFileParser()
                    parser.parse(body.decode('utf-8','replace').splitlines())
                    value=(parser,float(parser.crawl_delay(USER_AGENT) or parser.crawl_delay('*') or 0))
                self.robots_cache[origin]=value
                return value
        raise RobotsDenied('too many redirects in robots.txt')
    def fetch(self,url,spool):
        """Return event dict. Caller owns database transitions and retry scheduling."""
        started=time.monotonic();wait_ms=0;final_url=url
        spool=Path(spool);spool.mkdir(parents=True,exist_ok=True)
        try:
            for _ in range(6):
                host=safe_url(final_url,self.dns_check)
                parser,crawl_delay=self._robots(final_url)
                if parser and not parser.can_fetch(USER_AGENT,final_url):
                    return {'outcome':'blocked','error':'robots disallow','wait_ms':wait_ms,
                            'elapsed_ms':int((time.monotonic()-started)*1000)}
                response,w=self._request_with_delay(final_url,host,crawl_delay)
                wait_ms+=w
                if response.status_code in (301,302,303,307,308):
                    location=response.headers.get('Location','')
                    response.close()
                    if not location:return {'outcome':'failed','error':'redirect without location','wait_ms':wait_ms}
                    final_url=urljoin(final_url,location)
                    continue
                break
            else:return {'outcome':'failed','error':'too many redirects','wait_ms':wait_ms}
            with response:
                code=response.status_code
                base={'http_status':code,'wait_ms':wait_ms,'elapsed_ms':int((time.monotonic()-started)*1000)}
                if code in (429,500,502,503,504):
                    base.update(outcome='retry',error=f'HTTP {code}',
                                retry_after=retry_after(response.headers.get('Retry-After')))
                    self.limiter.postpone(host,base['retry_after'] or 0)
                    return base
                if code in (401,403):return dict(base,outcome='blocked',error=f'HTTP {code}')
                if code in (404,410):return dict(base,outcome='skipped',error=f'HTTP {code}')
                if code!=200:return dict(base,outcome='failed',error=f'HTTP {code}')
                expected=response.headers.get('Content-Length')
                # requests.iter_content decodes HTTP Content-Encoding. A compressed
                # transfer length differs from the uncompressed document length.
                encoded=(response.headers.get('Content-Encoding','').strip().lower()
                         not in ('','identity'))
                if expected and expected.isdigit() and not encoded and int(expected)>self.max_bytes:
                    return dict(base,outcome='skipped',error='file exceeds max size')
                chunks=response.iter_content(chunk_size=65536)
                prefix=next(chunks,b'')
                mime=response.headers.get('Content-Type','')
                category,mime=kind(mime,final_url,prefix)
                if category!='file':
                    outcome={'html':'html_deferred','image':'image_deferred'}.get(category,'skipped')
                    return dict(base,outcome=outcome,mime=mime,
                                error=None if outcome.endswith('_deferred') else 'unsupported media')
                filename=Path(unquote(urlparse(final_url).path)).name[:140] or 'download'
                fd,tmp=tempfile.mkstemp(dir=spool,prefix='.downloading-')
                size=0;sha=hashlib.sha256();md5=hashlib.md5()
                try:
                    with os.fdopen(fd,'wb') as f:
                        if prefix:
                            size+=len(prefix);sha.update(prefix);md5.update(prefix);f.write(prefix)
                        if size>self.max_bytes:raise ValueError('max file size exceeded')
                        for chunk in chunks:
                            if not chunk:continue
                            size+=len(chunk)
                            if size>self.max_bytes:raise ValueError('max file size exceeded')
                            sha.update(chunk);md5.update(chunk);f.write(chunk)
                        f.flush();os.fsync(f.fileno())
                    if expected and expected.isdigit() and not encoded and int(expected)!=size:
                        raise IOError(f'content length mismatch {expected} != {size}')
                    if size==0:raise IOError('zero byte document')
                    digest=sha.hexdigest()
                    dest=spool/digest
                    if dest.exists():os.unlink(tmp)
                    else:os.replace(tmp,dest)
                    return dict(base,outcome='staged',sha256=digest,md5=md5.hexdigest(),size=size,
                                mime=mime,filename=filename,path=str(dest),bytes_received=size,
                                elapsed_ms=int((time.monotonic()-started)*1000))
                except BaseException:
                    if os.path.exists(tmp):os.unlink(tmp)
                    raise
        except RobotsRetry as exc:
            self.limiter.postpone(host,exc.delay or 0)
            return {'outcome':'retry','http_status':exc.status,'retry_after':exc.delay,
                    'error':str(exc),'wait_ms':wait_ms,'elapsed_ms':int((time.monotonic()-started)*1000)}
        except (UnsafeURL,RobotsDenied) as exc:
            return {'outcome':'blocked','error':str(exc),'wait_ms':wait_ms,
                    'elapsed_ms':int((time.monotonic()-started)*1000)}
        except (requests.RequestException,IOError,ValueError,OSError,socket.gaierror) as exc:
            return {'outcome':'retry','error':str(exc)[:400],'wait_ms':wait_ms,
                    'elapsed_ms':int((time.monotonic()-started)*1000)}
    def _request_with_delay(self,url,host,crawl_delay):
        # A robots crawl-delay is the full interval since the previous request.
        # The limiter accounts for the previous robot fetch and persisted state.
        return self._request(url,minimum=crawl_delay,purpose='resource')
