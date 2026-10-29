"""Run locally once to create a Google Drive OAuth refresh token for the VPS."""
import argparse
import os
from pathlib import Path
from .drive import SCOPES
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--client-secrets',required=True)
    p.add_argument('--token',default='state/google_token.json')
    p.add_argument('--scope',choices=['file','drive'],default='file',
                   help='Use drive only when migrating existing Colab-created RIFT files')
    args=p.parse_args()
    from google_auth_oauthlib.flow import InstalledAppFlow
    scope=SCOPES if args.scope=='file' else ['https://www.googleapis.com/auth/drive']
    flow=InstalledAppFlow.from_client_secrets_file(args.client_secrets,scope)
    credentials=flow.run_local_server(port=0,access_type='offline',prompt='consent')
    path=Path(args.token);path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as out:out.write(credentials.to_json())
    print('Token created at',path,'(never commit it)')
if __name__=='__main__':main()
