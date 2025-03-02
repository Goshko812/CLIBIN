from flask import Flask, request, redirect, send_file, abort, render_template_string
import os
import uuid
import time
import threading
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pygments import highlight
from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter
import json

clibin = Flask(__name__)
limiter = Limiter(get_remote_address, app=clibin, default_limits=["10 per minute"])

DATA_DIR = "pastes"
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_EXPIRATION = 86400  # 1 day in seconds
MAX_PASTE_SIZE = 100 * 1024  # 100 KB max

def cleanup_old_pastes():
    while True:
        now = time.time()
        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as f:
                        metadata = json.loads(f.readline().strip())
                    if now > metadata.get("expires_at", 0):
                        os.remove(file_path)
                except:
                    os.remove(file_path)  # Remove corrupt files
        time.sleep(3600)  # Run cleanup every hour

threading.Thread(target=cleanup_old_pastes, daemon=True).start()

MANPAGE = """clibin(1)                          CLIBIN                          clibin(1)

NAME
    clibin: command line pastebin:

SYNOPSIS
    <command> | curl -F 'clibin=<-' https://example.com

DESCRIPTION
    add ?<hl> to resulting url for line numbers and syntax highlighting.
    add ?<hl>=language to specify language syntax
    add ?expires=<seconds> to set custom expiration time (default is 1 day)
    add ?onetime=true to make the paste expire after a single view

EXAMPLES
    ~$ cat hello-world.c | curl -F 'clibin=<-' https://example.com
    https://example.com/y94KD
    ~$ iceweasel https://example.com/y94KD?hl

    With helper function below...

    ~$ ps auxf | clibin
    https://example.com/jRxWf
    ~$ clibin netstat -tlnaepw
    https://example.com/tK2cF

"""

@clibin.route("/", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def index():
    if request.method == "POST":
        if "clibin" not in request.form:
            return "Missing 'clibin' field", 400
        
        paste_content = request.form["clibin"]
        if len(paste_content) > MAX_PASTE_SIZE:
            return "Paste too large", 400
        
        expires_in = request.args.get("expires", DEFAULT_EXPIRATION, type=int)
        expires_at = time.time() + expires_in
        onetime = request.args.get("onetime", "false").lower() == "true"
        
        paste_id = str(uuid.uuid4())[:6]  # Short ID
        if not re.match(r"^[a-zA-Z0-9_-]{1,10}$", paste_id):
            return abort(400)
        
        file_path = os.path.join(DATA_DIR, paste_id)
        
        with open(file_path, "w") as f:
            json.dump({"expires_at": expires_at, "onetime": onetime}, f)
            f.write("\n")  # Ensure metadata is on its own line
            f.write(paste_content)
        
        return f"https://{request.host}/{paste_id}\n"
    
    return MANPAGE, 200, {"Content-Type": "text/plain"}

@clibin.route("/<paste_id>", methods=["GET"])
@limiter.limit("10 per minute")
def retrieve(paste_id):
    if not re.match(r"^[a-zA-Z0-9_-]{1,10}$", paste_id):
        return abort(400)
    
    file_path = os.path.join(DATA_DIR, paste_id)
    if not os.path.exists(file_path):
        return abort(404)
    
    with open(file_path, "r") as f:
        metadata = json.loads(f.readline().strip())  # Read metadata
        paste_content = f.read()  # Only return the actual paste content
    
    if time.time() > metadata.get("expires_at", 0):
        os.remove(file_path)
        return abort(404)
    
    if metadata.get("onetime", False):
        os.remove(file_path)
    
    highlight_requested = request.args.get("hl")
    if highlight_requested is not None:
        try:
            lexer = get_lexer_by_name(highlight_requested) if highlight_requested else guess_lexer(paste_content)
        except:
            lexer = guess_lexer(paste_content)
        
        formatter = HtmlFormatter(style="monokai", linenos=True)
        highlighted_code = highlight(paste_content, lexer, formatter)
        style = formatter.get_style_defs(".highlight")  # Get CSS separately
        
        return render_template_string(
            """<!DOCTYPE html>
            <html>
                <head>
                    <style>
                        {{ style | safe }}
                        .highlight pre { color: white; }
                        .highlight .lineno { color: white !important; text-align: right; padding-right: 10px; }
                        .highlight table { width: 100%; border-spacing: 0; }
                        .highlight td { padding: 5px; }
                    </style>
                </head>
                <body>
                    {{ code | safe }}
                </body>
            </html>""",
            code=highlighted_code,
            style=style
        )
    return paste_content, 200, {"Content-Type": "text/plain"}

if __name__ == "__main__":
    clibin.run(host="0.0.0.0", port=5000)
