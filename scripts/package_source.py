"""Create a source-only archive for Kaggle/GitHub review; never include raw data."""
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
destination=root/'dist'/'inventory-intelligence-source.zip'
destination.parent.mkdir(exist_ok=True)
allowed_dirs={'src','configs','docs','tests','scripts','notebooks','.github'}
allowed_files={'README.md','LICENSE','pyproject.toml','requirements-lock.txt','.gitignore'}
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if not p.is_file() or '__pycache__' in rel.parts:continue
        if rel.parts[0] in allowed_dirs or str(rel) in allowed_files:
            archive.write(p,Path('inventory-intelligence')/rel)
print(destination)
