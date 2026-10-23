"""Freeze actual dataset bytes and current M1-M4/M6 source files."""
from pathlib import Path
from .common import *
from .dataset import verify_dataset

CONFIG_KEYS={'experiment_kind','model','model_parameters','prompt_version','schema_version','index_snapshot'}

def source_files(repo=REPO):
    paths=[]
    for name in ['m1-elk','m2-connectors','m3-schema','m4-mcp','m6-experiment']:
        for p in (repo/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.ps1','.sh','.toml','.yml'):
                paths.append(p)
    # Schema definitions and strict mappings are part of the frozen contract.
    paths += list((repo/'m3-schema/tracehunt_schema/schemas').glob('*.json'))
    paths += [repo/'m1-elk/index_template.json',repo/'m1-elk/raw_index_template.json']
    return {str(p.relative_to(repo)):file_sha(p) for p in sorted(set(paths))}

def validate_config(c):
    if not isinstance(c,dict) or set(c)!=CONFIG_KEYS:raise ValueError(f'config keys must be exactly {sorted(CONFIG_KEYS)}; credentials never belong here')
    if c['experiment_kind'] not in ['agent','typed_api_smoke']:raise ValueError('experiment_kind must be agent or typed_api_smoke')
    if not isinstance(c['model_parameters'],dict):raise ValueError('model_parameters must be an object')
    for k in CONFIG_KEYS-{'model_parameters'}:
        if not isinstance(c[k],str) or not c[k].strip() or any(x in c[k].lower() for x in ['todo','replace_me','pending']):
            raise ValueError(f'concrete configuration required: {k}')
    def secrets(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if any(s in k.lower() for s in ['password','secret','api_key','authorization','access_token']):raise ValueError('do not freeze credentials')
                secrets(v)
        elif isinstance(x,list):
            for v in x:secrets(v)
    secrets(c)

def freeze(dataset,config,assets,out):
    m=verify_dataset(dataset); c=read(config); validate_config(c)
    assets=[Path(p).resolve() for p in assets]
    if not assets:raise ValueError('freeze at least the actual prompt/run-protocol asset')
    if len({p.name for p in assets})!=len(assets):raise ValueError('asset names must be unique')
    if Path(out).resolve().is_relative_to(Path(dataset).resolve()):raise ValueError('freeze output must be outside dataset')
    p=Path(out)
    if p.exists():raise ValueError('freeze output exists; use a new path')
    f={'schema_version':2,'dataset_id':m['dataset_id'],'scenario':read(Path(dataset)/'scenario.json'),
        'configuration':c,'code_files':source_files(),'assets':{p.name:file_sha(p) for p in assets},
        'freeze_scope_note':'Local dataset and code bytes. External ES snapshot and collection continuity require separate verification.'}
    f['freeze_id']=payload_hash(f,'freeze_id');write(out,f)
    return f

def verify_freeze(manifest,dataset=None,config=None,assets=None,check_code=True):
    f=read(manifest)
    if payload_hash(f,'freeze_id')!=f['freeze_id']:raise ValueError('freeze manifest hash mismatch')
    validate_config(f['configuration'])
    if dataset is not None and verify_dataset(dataset)['dataset_id']!=f['dataset_id']:raise ValueError('frozen dataset mismatch')
    if config is not None and read(config)!=f['configuration']:raise ValueError('model/experiment configuration changed')
    if check_code and source_files()!=f['code_files']:raise ValueError('M1-M4/M6 source files changed after freeze')
    if assets is not None:
        actual={Path(p).name:file_sha(p) for p in assets}
        if actual!=f['assets']:raise ValueError('prompt/protocol assets changed')
    return f
