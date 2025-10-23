from flask import Flask, request, send_from_directory,jsonify
from werkzeug.utils import secure_filename
import subprocess
import os
import json
import uuid
import shutil
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from flask import Flask, send_from_directory
app = Flask(__name__)
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')
@app.route('/index.html')
def index_html():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def style():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def script():
    return send_from_directory('.', 'script.js')
@app.route('/history.html')
def history():
    return send_from_directory('.', 'history.html')


import tempfile
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        file = request.files.get('codefile')
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        #filename = file.filename
        filename = secure_filename(file.filename)
        ext = filename.split('.')[-1].lower()

        # Detect language
        if filename.endswith('.py'):
            detected_language = 'Python'
        elif filename.endswith(('.js', '.ts', '.tsx', '.jsx')):
            detected_language = 'JavaScript'
        else:
            detected_language = 'Unknown'

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + ext) as temp_file:
            temp_file.write(file.read())
            temp_file.flush()
            filepath = temp_file.name
        eslint_path = os.path.join(os.getcwd(), f"{uuid.uuid4().hex}.js")
        shutil.copy(filepath, eslint_path)

        results = []
        high = medium = low = 0

        if detected_language == 'Python':
            result = subprocess.run(['bandit', '-r', filepath, '-f', 'json', '-q'],
                                    capture_output=True, text=True)
            data = json.loads(result.stdout)
            issues = data.get('results', [])
            summary = data.get('metrics', {}).get(filepath, {})
            for issue in issues:
                sev = issue['issue_severity'].upper()
                if sev == 'HIGH': high += 1
                elif sev == 'MEDIUM': medium += 1
                elif sev == 'LOW': low += 1
                results.append({
                    "severity": sev,
                    "ruleId": issue['test_id'],
                    "message": issue['issue_text'],
                    "line": issue.get('line_number', '?'),
                    "code": issue['code']
                })
            timestamp = data.get('generated_at', 'N/A')
        elif detected_language == 'JavaScript':
            eslint_config_path = os.path.abspath("codeDefender.config.mjs")
            # Use the already-saved temp file
            print("📄 Uploaded file contents:")
            with open(filepath, 'r', encoding='utf-8') as f:
                print(f.read())
            print("📁 ESLint analyzing file:", filepath)
            result = subprocess.run(['npx', 'eslint',  eslint_path,'--config',eslint_config_path,'--no-ignore', '--no-warn-ignored',  '-f', 'json'],
                                    capture_output=True, encoding='utf-8', shell=True)
            print("📍 ESLint return code:", result.returncode)
            print("📍 ESLint stdout:", result.stdout)
            print("📍 ESLint stderr:", result.stderr)
            
            if result.returncode != 0 and not result.stdout:
                return jsonify({"error": "ESLint failed", "stderr": result.stderr}), 500
            if not result.stdout.strip():
                return jsonify({"error": "ESLint returned empty output", "stderr": result.stderr}), 500
            eslint_data = json.loads(result.stdout)
            from datetime import datetime
            timestamp = datetime.now().strftime('%H:%M:%S')
            for file_result in eslint_data:
                for msg in file_result.get('messages', []):
                    
                    sev = 'HIGH' if msg['severity'] == 2 else 'MEDIUM' if msg['severity'] == 1 else 'LOW'
                    if sev == 'HIGH': high += 1
                    elif sev == 'MEDIUM': medium += 1
                    elif sev == 'LOW': low += 1
                    results.append({
                        "severity": sev,
                        "ruleId": msg.get('ruleId', 'N/A'),
                        "message": msg.get('message', 'No description'),
                        "line": msg.get('line', '?'),
                        "code": file_result.get('source', '')
                    })
        elif filename.endswith(('.c', '.cpp')):
            detected_language = 'C++' if filename.endswith('.cpp') else 'C'
            import re
            from datetime import datetime
            timestamp = datetime.now().strftime('%H:%M:%S')

            with open(filepath, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()

            result = subprocess.run([
                'cppcheck', '--enable=all', '--quiet', '--template=gcc', filepath
                ], capture_output=True, encoding='utf-8', shell=True)

            for line in result.stderr.splitlines():
                match = re.match(r'^(.*?):(\d+):\s*(\w+):\s*(.*)$', line)
                if not match:
                    continue

                _, raw_line_num, severity, message = match.groups()
                line_num = raw_line_num if raw_line_num.isdigit() and int(raw_line_num) > 0 else "?"

                if "[checkersReport]" in message or "[missingIncludeSystem]" in message:
                     continue

                sev = 'HIGH' if severity == 'error' else 'MEDIUM' if severity == 'warning' else 'LOW'
                if sev == 'HIGH': high += 1
                elif sev == 'MEDIUM': medium += 1
                elif sev == 'LOW': low += 1

                try:
                    line_index = int(line_num) - 1
                    code_line = file_lines[line_index].strip() if 0 <= line_index < len(file_lines) else ""
                except:
                    code_line = ""

                results.append({
                    "severity": sev,
                    "ruleId": "cppcheck",
                    "message": message,
                    "line": line_num,
                     "code": code_line
                })
    
            

        else:
            return jsonify({"error": "Unsupported file type"}), 400
        print("📦 Final results:", results)
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        return jsonify({
            "filename": filename,
            "language": detected_language,
            "summary": {
                "high": high,
                "medium": medium,
                "low": low,
                "time": timestamp
            },
            "results": results
        })

    except Exception as e:
        import traceback
        print("📍 Exception Trace:")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500
        
    finally:
        try:
            os.remove(filepath)
        except Exception:
            pass
        

if __name__ == '__main__':
    app.run(debug=True)