# app_short.py
# Aplikasi demo singkat: upload (no validation), download (path traversal), simple SQLi
from flask import Flask, request, send_file, render_template_string
import sqlite3, os, hashlib

app = Flask(__name__)
UPLOAD_DIR = "uploads"
DB = "si_demo.db"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# init DB kecil
def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, name TEXT, content TEXT)")
        c.execute("INSERT INTO documents (name, content) VALUES ('doc1','Isi dokumen 1')")
        conn.commit()
        conn.close()

@app.route('/')
def index():
    return "<h3>Sistem Informasi - Demo Singkat (tanpa login)</h3>" \
           "<ul><li><a href='/upload'>Upload</a></li><li><a href='/download'>Download</a></li>" \
           "<li><a href='/doc?id=1'>Ambil doc (SQLi demo)</a></li></ul>"

# 1) Upload (no extension/type check)
@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'GET':
        html = '''
        <h4>Upload file (vulnerable)</h4>
        <form method="post" enctype="multipart/form-data"><input type="file" name="f"/><button>Upload</button></form>
        '''
        return render_template_string(html)
    f = request.files.get('f')
    if not f:
        return "No file", 400
    # simpan langsung dengan nama asli (bisa berisi ../)
    path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(path)
    return f"Saved: {path}"

# 2) Download (path traversal possible)
@app.route('/download', methods=['GET','POST'])
def download():
    if request.method == 'GET':
        return '''
          <form method="post"><label>filename: <input name="fn"></label><button>Get</button></form>
        '''
    fn = request.form.get('fn','')
    # RENTAN: langsung menggabungkan path user-controlled
    path = os.path.join(UPLOAD_DIR, fn)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Not found", 404

# 3) Ambil dokumen dari DB — vulnerable to SQL injection (string formatting)
@app.route('/doc')
def doc():
    doc_id = request.args.get('id', '')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # SENGAJA RENTAN: menggunakan formatting langsung -> SQLi
    q = "SELECT id, name, content FROM documents WHERE id = %s" % doc_id
    try:
        c.execute(q)
        r = c.fetchone()
    except Exception as e:
        return f"DB error: {e}"
    finally:
        conn.close()
    if r:
        return f"<h4>{r[1]}</h4><pre>{r[2]}</pre>"
    return "No doc", 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5002)
