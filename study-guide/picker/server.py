"""Read-only localhost gallery of the eight bundled study-guide themes."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import theme

HERE = Path(__file__).resolve().parent
ORDER = ('dark', 'graphite', 'cobalt', 'obsidian', 'paper', 'sepia', 'ice', 'mono')

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, content_type):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == "/":
            return self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if route.startswith("/fonts/"):
            name = route.removeprefix("/fonts/")
            if name != Path(name).name or not name.endswith(".woff2"):
                return self.send(404, "not found", "text/plain")
            file = HERE / "fonts" / name
            if file.is_file():
                return self.send(200, file.read_bytes(), "font/woff2")
        if route.startswith("/sample/"):
            name = route.removeprefix("/sample/")
            if name in ORDER:
                cfg = json.loads((HERE / "presets" / f"{name}.json").read_text(encoding="utf-8"))
                mode = cfg["themes"][0]
                pal = cfg[mode]
                css = theme.emit_css(cfg, mode).replace('url("fonts/', 'url("/fonts/').replace("url('fonts/", "url('/fonts/")
                sample = f"""<!doctype html><html lang="en"><meta charset="utf-8">
                <style>{css}
                body{{margin:0;padding:22px;background:{pal['base']};background-image:linear-gradient(160deg,{pal['gradient']['from']},{pal['gradient']['to']});color:{pal['text']}}}
                h1{{font-size:23px;color:{pal['strong']}}} .sample-label{{color:{pal['accent']}}}
                </style><body><div class="sample-label">{name.upper()} / STUDY GUIDE</div>
                <h1>Understanding the topic</h1><p>A concise explanation, with clear steps and readable labels.</p>
                <div class="card"><div class="card-h">METHOD</div><div class="card-b">1. Identify the given values.<br>2. Apply the formula.<br>3. Check the result.</div></div>
                <div class="work"><div class="work-h">WORKED EXAMPLE</div><div class="work-b">Result = 24 units</div></div>
                <div class="code"><div class="code-h"><span class="name">example.c</span></div><pre>return result;</pre></div>
                <table class="data"><tr><th>Quantity</th><th>Value</th></tr><tr><td>Time</td><td>O(n)</td></tr></table>
                </body></html>"""
                return self.send(200, sample, "text/html; charset=utf-8")
        self.send(404, "not found", "text/plain")

    def do_POST(self):
        self.send(405, "Read-only gallery. Tell the agent your theme choice in chat.", "text/plain")

if __name__ == "__main__":
    for port in range(8745, 8757):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    else:
        raise SystemExit("No free gallery port in 8745-8756")
    print(f"theme gallery: http://127.0.0.1:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
