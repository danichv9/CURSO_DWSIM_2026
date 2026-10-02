from pathlib import Path
import zipfile
root=Path(__file__).resolve().parent
web=root/'web'
html=(web/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','<style>'+(web/'styles.css').read_text()+'</style>').replace('<script defer src="model.js"></script><script defer src="app.js"></script>','')
html=html.replace('</body>','<script>'+(web/'model.js').read_text()+'</script><script>'+(web/'app.js').read_text()+'</script></body>')
(root/'Syngas_Lab.html').write_text(html)
with zipfile.ZipFile(root/'Syngas_Lab.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix not in ['.zip','.pyc'] and '__pycache__' not in p.parts:
   z.write(p,p.relative_to(root))
print('HTML autónomo y ZIP generados')
