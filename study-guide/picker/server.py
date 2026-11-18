"""Read-only localhost gallery of the bundled study-guide themes."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import theme

HERE = Path(__file__).resolve().parent

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
            if name in theme.PRESET_NAMES:
                cfg = json.loads((HERE / "presets" / f"{name}.json").read_text(encoding="utf-8"))
                mode = cfg["themes"][0]
                pal = cfg[mode]
                css = theme.emit_css(cfg, mode).replace('url("fonts/', 'url("/fonts/').replace("url('fonts/", "url('/fonts/")
                sample = f"""<!doctype html><html lang="en"><meta charset="utf-8">
                <style>{css}
                body{{margin:0;padding:22px;background:{pal['base']};color:{pal['text']}}}
                h1{{font-size:23px;color:{pal['strong']}}} .sample-label{{color:{pal['accent']}}}
                </style><body data-theme="{name}"><div class="sample-label">{name} / study guide</div>
                <h1>Understanding the topic</h1><p>A concise explanation, with clear steps and readable labels.</p>
                <div class="card"><div class="card-h">Method</div><div class="card-b">1. Identify the given values.<br>2. Apply the formula.<br>3. Check the result.</div></div>
                <div class="work"><div class="work-h">Worked example</div><div class="work-b">Result = 24 units</div></div>
                <div class="code"><div class="code-h"><span class="name">example.c</span></div><pre>return result;</pre></div>
                <table class="data"><tr><th>Quantity</th><th>Value</th></tr><tr><td>Time</td><td>O(n)</td></tr></table>
                </body></html>"""
                if name == "paperx":
                    sample = f'''<!doctype html><html lang="en"><meta charset="utf-8"><style>{css}
                    body{{margin:0;padding:22px;background:white;color:#171717}}h1{{font-size:23px}}
                    </style><body data-theme="paperx"><h1>Understanding the topic</h1>
                    <div class="px-block px-theory"><p>A concise explanation, with clear steps and readable labels.</p></div>
                    <div class="px-block px-math"><div class="eq">Result = rate × time</div></div>
                    <div class="px-block px-table"><table class="data"><tr><th>Quantity</th><th>Value</th></tr><tr><td>Time</td><td>O(n)</td></tr></table></div>
                    <div class="px-block px-note"><p>The formula assumes a constant rate.</p></div></body></html>'''
                if name == "pdfcn":
                    sample = f"""<!doctype html><html lang="en"><meta charset="utf-8"><style>{css}
                    body{{padding:22px}}
                    </style><body data-theme="pdfcn">
                    <div class="unit-head"><h1>How a memory hierarchy works</h1></div>
                    <h2 class="sec"><span class="topic-num">1.1</span> Why a cache saves time</h2>
                    <p>The cache keeps recently used blocks close to the CPU, so a repeated
                    access can often avoid the trip to main memory.</p>
                    <h3 class="sub">Follow one access</h3>
                    <p>When the requested block is already present, the CPU reads it from
                    the cache. A miss fetches the block from the next level.</p>
                    <div class="work"><div class="work-h">Average access time</div>
                    <div class="work-b"><span class="cont">A 2 ns lookup plus a 5% chance of
                    an 80 ns miss penalty averages 6 ns.</span></div></div>
                    <table class="data"><thead><tr><th>Result</th><th>Action</th></tr></thead>
                    <tbody><tr><td>Hit</td><td>Read the cached block</td></tr>
                    <tr><td>Miss</td><td>Fetch from the next level</td></tr></tbody></table>
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
