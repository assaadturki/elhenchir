# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('models', 'models'),
    ('config.py', '.'),
]

if Path('.env').exists():
    datas.append(('.env', '.'))

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask', 'flask_sqlalchemy', 'flask_login', 'flask_migrate',
        'flask.templating', 'jinja2', 'jinja2.ext', 'werkzeug',
        'werkzeug.routing', 'werkzeug.utils', 'click', 'itsdangerous',
        'sqlalchemy', 'sqlalchemy.dialects.sqlite', 'sqlalchemy.orm',
        'sqlalchemy.ext.declarative', 'bcrypt', 'openpyxl',
        'openpyxl.styles', 'openpyxl.utils', 'dotenv', 'email_validator',
        'webview', 'webview.platforms.winforms', 'webview.platforms.edgechromium',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'tkinter'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='FarmManagement',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon='farmer.ico',  # Icone de l'application
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[],
    name='FarmManagement',
)
