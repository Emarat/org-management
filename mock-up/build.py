#!/usr/bin/env python3
"""Compile the Claude Design canvas in design/ into a standalone static page.

The .dc.html sources stay the single source of truth: this script reads their
markup, runs their real `renderVals()` through node, expands the design-canvas
directives (`sc-for`, `sc-if`, `dc-import`, `{{ expr }}`, `style-hover`) and
writes plain HTML/CSS that opens straight from disk — no runtime, no network
beyond the Google Fonts link.

    python3 build.py                      # -> index.html
    python3 build.py --accent '#3B6FE0'   # recolour the accent prop
    python3 build.py --fit center         # centre at 1:1 instead of scaling to fill
    python3 build.py -o out/console.html
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN_DIR = os.path.join(HERE, "design")

ENTRY = "Atlas Console.dc.html"
PAGE_TITLE = "Atlas Console — OrgMS UI mockups"

# The canvas is drawn at a fixed size: 1440px artboards plus the 56px gutters
# the root frame sets. Everything downstream scales off this one number.
CANVAS_WIDTH = 1552


# --------------------------------------------------------------------------
# .dc.html parsing
# --------------------------------------------------------------------------

class Component:
    """One parsed .dc.html file: helmet, template markup, logic script, props."""

    def __init__(self, name: str, source: str):
        self.name = name
        self.source = source
        self.helmet = _extract_tag(source, "helmet") or ""
        template = _extract_tag(source, "x-dc")
        if template is None:
            raise SystemExit(f"{name}: no <x-dc> block found")
        # The helmet lives inside <x-dc> but is head content, not body content.
        self.template = template.replace(_wrap_tag(source, "helmet") or "", "", 1).strip()
        self.script, props_attr = _extract_dc_script(source)
        self.props_schema = json.loads(html.unescape(props_attr)) if props_attr else {}

    def defaults(self) -> dict:
        out = {}
        for key, spec in self.props_schema.items():
            if key.startswith("$"):
                continue
            out[key] = spec.get("default")
        return out

    def render_vals(self, props: dict) -> dict:
        return _run_render_vals(self.name, self.script, props)


def _wrap_tag(src: str, tag: str) -> str | None:
    """Return the full `<tag ...>...</tag>` slice, attributes included."""
    m = re.search(rf"<{tag}\b[^>]*>", src)
    if not m:
        return None
    close = src.rindex(f"</{tag}>") + len(tag) + 3
    return src[m.start():close]


def _extract_tag(src: str, tag: str) -> str | None:
    """Return the inner content of the first `<tag>` .. last `</tag>`."""
    m = re.search(rf"<{tag}\b[^>]*>", src)
    if not m:
        return None
    close = src.rindex(f"</{tag}>")
    return src[m.end():close]


def _extract_dc_script(src: str) -> tuple[str, str | None]:
    m = re.search(r"<script[^>]*\bdata-dc-script\b[^>]*>", src)
    if not m:
        return "", None
    end = src.index("</script>", m.end())
    props = re.search(r'data-props="([^"]*)"', m.group(0))
    return src[m.end():end], (props.group(1) if props else None)


def _run_render_vals(name: str, script: str, props: dict) -> dict:
    """Execute the component's own JS logic so the data never has to be ported."""
    harness = (
        "class DCLogic { constructor(props) { this.props = props || {}; } }\n"
        f"{script}\n"
        f"const __props = {json.dumps(props)};\n"
        "process.stdout.write(JSON.stringify(new Component(__props).renderVals()));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        proc = subprocess.run([_node(), path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        raise SystemExit(f"{name}: renderVals() failed\n{proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _node() -> str:
    for candidate in ("node", "nodejs"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True, check=True)
            return candidate
        except (OSError, subprocess.CalledProcessError):
            continue
    raise SystemExit("node is required to evaluate the .dc.html logic scripts")


# --------------------------------------------------------------------------
# Template expansion
# --------------------------------------------------------------------------

EXPR = re.compile(r"\{\{\s*([A-Za-z_$][\w$]*(?:\.[\w$]+)*)\s*\}\}")
BLOCK_TAGS = ("sc-for", "sc-if", "dc-import")
OPEN_TAG = re.compile(r"<(sc-for|sc-if|dc-import)\b")


class Renderer:
    def __init__(self, design_dir: str, accent: str | None):
        self.design_dir = design_dir
        self.accent = accent
        self._cache: dict[str, Component] = {}

    def component(self, name: str) -> Component:
        if name not in self._cache:
            path = os.path.join(self.design_dir, f"{name}.dc.html")
            if not os.path.exists(path):
                raise SystemExit(f"imported component not found: {path}")
            with open(path, encoding="utf-8") as fh:
                self._cache[name] = Component(name, fh.read())
        return self._cache[name]

    def render(self, name: str, props: dict | None = None) -> tuple[str, str]:
        """Render a component to (head_html, body_html)."""
        comp = self.component(name)
        resolved = comp.defaults()
        resolved.update({k: v for k, v in (props or {}).items() if v is not None})
        if self.accent and "accent" in comp.props_schema:
            resolved["accent"] = self.accent
        ctx = comp.render_vals(resolved)
        return comp.helmet, self.expand(comp.template, ctx)

    def expand(self, markup: str, ctx: dict) -> str:
        out: list[str] = []
        pos = 0
        while True:
            m = OPEN_TAG.search(markup, pos)
            if not m:
                out.append(substitute(markup[pos:], ctx))
                return "".join(out)
            out.append(substitute(markup[pos:m.start()], ctx))
            tag = m.group(1)
            attrs, after_open = read_open_tag(markup, m.start())
            inner, pos = read_block(markup, tag, after_open)
            out.append(self.expand_block(tag, attrs, inner, ctx))

    def expand_block(self, tag: str, attrs: dict, inner: str, ctx: dict) -> str:
        if tag == "sc-for":
            items = resolve(attrs["list"], ctx)
            if items is None:
                return ""
            var = attrs.get("as", "item")
            parts = []
            for item in items:
                scope = dict(ctx)
                scope[var] = item
                parts.append(self.expand(inner, scope))
            return "".join(parts)

        if tag == "sc-if":
            return self.expand(inner, ctx) if truthy(resolve(attrs["value"], ctx)) else ""

        # dc-import: every attribute except the hints is a prop for the child.
        name = attrs.pop("name")
        props = {k: substitute(v, ctx) for k, v in attrs.items() if not k.startswith("hint-")}
        _, body = self.render(name, props)
        return body


def read_open_tag(markup: str, start: int) -> tuple[dict, int]:
    """Parse `<tag a="1" b="2">` starting at `start`; return attrs and end index."""
    end = start
    quote = None
    while end < len(markup):
        ch = markup[end]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == ">":
            break
        end += 1
    open_tag = markup[start:end + 1]
    attrs = {k: html.unescape(v) for k, v in re.findall(r'([\w:-]+)="([^"]*)"', open_tag)}
    attrs.pop("hint-size", None)
    attrs.pop("hint-placeholder-count", None)
    attrs.pop("hint-placeholder-val", None)
    return attrs, end + 1


def read_block(markup: str, tag: str, start: int) -> tuple[str, int]:
    """Return (inner markup, index after `</tag>`), honouring nesting."""
    depth = 1
    pos = start
    pattern = re.compile(rf"<(/?){tag}\b")
    while depth:
        m = pattern.search(markup, pos)
        if not m:
            raise SystemExit(f"unclosed <{tag}> in template")
        if m.group(1):
            depth -= 1
            if depth == 0:
                close_end = markup.index(">", m.end()) + 1
                return markup[start:m.start()], close_end
        else:
            depth += 1
        pos = m.end()
    raise SystemExit(f"unclosed <{tag}> in template")


def resolve(expr: str, ctx: dict):
    """Resolve `{{ a.b }}` (or a bare `a.b` path) against the context."""
    m = EXPR.fullmatch(expr.strip())
    path = (m.group(1) if m else expr).split(".")
    value = ctx
    for key in path:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def substitute(text: str, ctx: dict) -> str:
    def repl(m: re.Match) -> str:
        value = resolve(m.group(1), ctx)
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    return EXPR.sub(repl, text)


def truthy(value) -> bool:
    return value not in (None, False, "", "false", 0)


# --------------------------------------------------------------------------
# Walking the compiled markup
# --------------------------------------------------------------------------

TAG_OPEN = re.compile(r"<([a-zA-Z][\w-]*)\b")
VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "source", "wbr"}


def end_of_open_tag(fragment: str, start: int) -> int:
    """Index just past the `>` that closes the open tag beginning at `start`."""
    i, quote = start, None
    while i < len(fragment):
        ch = fragment[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == ">":
            return i + 1
        i += 1
    raise SystemExit("unterminated tag in compiled markup")


def top_level_elements(fragment: str) -> list[str]:
    """Split a fragment into its top-level elements, ignoring text and comments."""
    out: list[str] = []
    pos = 0
    while True:
        m = TAG_OPEN.search(fragment, pos)
        if not m:
            return out
        name = m.group(1)
        open_end = end_of_open_tag(fragment, m.start())
        if name in VOID_TAGS or fragment[open_end - 2] == "/":
            out.append(fragment[m.start():open_end])
            pos = open_end
            continue
        depth, cursor = 1, open_end
        pattern = re.compile(rf"<(/?){name}\b")
        while depth:
            mm = pattern.search(fragment, cursor)
            if not mm:
                raise SystemExit(f"unclosed <{name}> in compiled markup")
            if mm.group(1):
                depth -= 1
                cursor = fragment.index(">", mm.end()) + 1
            else:
                depth += 1
                cursor = end_of_open_tag(fragment, mm.start())
        out.append(fragment[m.start():cursor])
        pos = cursor


def unwrap(element: str) -> tuple[str, str]:
    """Split an element into (open tag, inner html)."""
    open_end = end_of_open_tag(element, 0)
    close_start = element.rindex("</")
    return element[:open_end], element[open_end:close_start]


# --------------------------------------------------------------------------
# style-hover -> real CSS
# --------------------------------------------------------------------------

def lift_hover_styles(body: str) -> tuple[str, str]:
    rules: dict[str, str] = {}
    out: list[str] = []
    pos = 0
    for m in re.finditer(r'\s*style-hover="([^"]*)"', body):
        decls = html.unescape(m.group(1)).strip().rstrip(";")
        cls = rules.setdefault(decls, f"dc-h{len(rules) + 1}")
        out.append(body[pos:m.start()])
        out.append(f' class="{cls}"')
        pos = m.end()
    out.append(body[pos:])
    css = "\n".join(f".{cls}:hover{{{decls}}}" for decls, cls in rules.items())
    return "".join(out), css


# --------------------------------------------------------------------------

def clean_helmet(helmet: str) -> str:
    """Drop canvas-editor-only bits; keep the fonts, styles and keyframes."""
    helmet = re.sub(r'<meta name="design_doc_mode"[^>]*>\s*', "", helmet)
    helmet = re.sub(
        r'<template id="__bundler_thumbnail".*?</template>\s*', "", helmet, flags=re.S
    )
    return helmet.strip()


# --------------------------------------------------------------------------
# Prototype: one screen at a time, reached through the sidebar
# --------------------------------------------------------------------------

# Sidebar label -> screen id. Every item in the sidebar has to land somewhere,
# otherwise clicking it in the demo does nothing and reads as broken.
NAV = {
    "Dashboard": "dashboard",
    "Customers": "customers",
    "Inventory": "inventory",
    "Suppliers": "suppliers",
    "Expenses": "expenses",
    "Sales": "sales",
    "Submit Bill": "submit-bill",
    "My Bills": "my-bills",
    "Review Bills": "review-bills",
    "Reports": "reports",
    "Settings": "settings",
}

SHELL_OPEN = (
    '<div style="width:1440px;height:{height};display:flex;border-radius:16px;'
    "overflow:hidden;background:#FCFAF8;box-shadow:0 1px 2px rgba(26,23,20,.06),"
    '0 18px 50px -28px rgba(26,23,20,.28)">'
)

# The canvas has no Expenses artboard — expenses only appear on the dashboard
# and in Reports. Say so on the screen rather than leaving a dead menu item.
EXPENSES_PLACEHOLDER = """
<div style="max-width:560px;background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px;display:flex;flex-direction:column;gap:10px">
  <div style="font:400 11px/1 'IBM Plex Mono',monospace;letter-spacing:.07em;color:#A29A91">EXPENSES</div>
  <h2 style="margin:0;font:600 20px/1.2 'Plus Jakarta Sans',sans-serif;letter-spacing:-.02em;color:#1A1714">Not drawn in this mockup round</h2>
  <p style="margin:0;font:400 13px/1.6 'Plus Jakarta Sans',sans-serif;color:#7C736A">Expense entries show up on the Dashboard (recent expenses, monthly total) and in Reports &amp; ledger (breakdown by category, full debit list). A dedicated Expenses screen is the next one to design.</p>
</div>
"""


def shell(renderer: "Renderer", active: str, inner: str, height: str = "640px") -> str:
    """Wrap loose panels in the same app frame the drawn screens use."""
    _, sidebar = renderer.render("Sidebar", {"active": active})
    return (
        SHELL_OPEN.format(height=height)
        + sidebar
        + '<div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:16px;'
        'padding:24px 28px;overflow:auto">'
        + inner
        + "</div></div>"
    )


def build_screens(renderer: "Renderer", body: str) -> tuple[str, str]:
    """Turn the stacked canvas into addressable screens. Returns (open tag, screens)."""
    root_open, root_inner = unwrap(top_level_elements(body)[0])
    sections = [el for el in top_level_elements(root_inner) if el.startswith("<section")]
    if len(sections) != 9:
        raise SystemExit(f"expected 9 canvas sections, found {len(sections)}")

    # Each <section> is a caption row followed by one or two artboard rows.
    rows = [top_level_elements(unwrap(s)[1])[1:] for s in sections]
    login, dashboard, customers, inventory, suppliers, sales, bills, reports, settings = rows

    submit_panel, my_bills_panel = top_level_elements(unwrap(bills[1])[1])

    screens = [
        ("login", login[0]),
        ("dashboard", dashboard[0]),
        ("customers", customers[0]),
        ("inventory", inventory[0]),
        ("suppliers", suppliers[0]),
        ("expenses", shell(renderer, "Expenses", EXPENSES_PLACEHOLDER)),
        ("sales", sales[0]),
        ("submit-bill", shell(renderer, "Submit Bill", submit_panel)),
        ("my-bills", shell(renderer, "My Bills", my_bills_panel)),
        ("review-bills", bills[0]),
        ("reports", reports[0]),
        ("settings", settings[0]),
    ]
    markup = "\n".join(
        f'<div class="screen" data-screen="{sid}">\n{content}\n</div>'
        for sid, content in screens
    )
    return root_open, markup


PROTOTYPE_CSS = """
.screen{display:none}
.screen.is-active{display:block}
[data-nav],[data-signout],#screen-login button{cursor:pointer}
"""

# Sign in lands on the dashboard; from there every sidebar item is live, and the
# account row at the bottom of the sidebar signs back out. The hash keeps the
# browser's back button working, which matters when demoing the flow.
ROUTER_JS = """
(function () {
  var NAV = %(nav)s;
  var screens = {};
  var order = [];
  Array.prototype.forEach.call(document.querySelectorAll('.screen'), function (el) {
    screens[el.dataset.screen] = el;
    order.push(el.dataset.screen);
  });

  function show(id) {
    if (!screens[id]) id = order[0];
    order.forEach(function (key) {
      screens[key].classList.toggle('is-active', key === id);
    });
    if (location.hash.slice(1) !== id) location.hash = id;
    window.scrollTo(0, 0);
  }

  Array.prototype.forEach.call(document.querySelectorAll('.screen [data-nav]'), function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var target = NAV[a.getAttribute('data-nav')];
      if (target) show(target);
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll('.screen [data-signout]'), function (el) {
    el.addEventListener('click', function () { show('login'); });
  });

  Array.prototype.forEach.call(
    document.querySelectorAll('[data-screen="login"] button'), function (btn) {
      btn.addEventListener('click', function () { show('dashboard'); });
    });

  window.addEventListener('hashchange', function () { show(location.hash.slice(1)); });
  show(location.hash.slice(1) || 'login');
})();
"""


# --------------------------------------------------------------------------
# Fitting the fixed-width canvas to the viewport
# --------------------------------------------------------------------------

FIT_CSS = """
html{background:#EDEAE5}
body{overflow-x:hidden}
#dc-canvas{width:%(w)spx;margin:0 auto;transform-origin:top left}
"""

# Scales the canvas so it always spans the window — up on wide monitors, down on
# narrow ones — instead of sitting at 1440px against the left edge. `zoom` is
# used where available because it reflows properly; `transform` is the fallback
# and needs the body height compensated by hand.
FIT_JS = """
(function () {
  var W = %(w)s;
  var canvas = document.getElementById('dc-canvas');
  var useZoom = !!(window.CSS && CSS.supports && CSS.supports('zoom', '1'));
  function fit() {
    var scale = document.documentElement.clientWidth / W;
    if (useZoom) {
      canvas.style.zoom = scale;
    } else {
      canvas.style.transform = 'scale(' + scale + ')';
      document.body.style.height = canvas.getBoundingClientRect().height + 'px';
    }
  }
  fit();
  window.addEventListener('resize', fit);
})();
"""


def fit_layer(mode: str) -> tuple[str, str, bool]:
    """Return (extra css, trailing script, wrap-in-#dc-canvas) for a fit mode."""
    if mode == "none":
        return "", "", False
    css = FIT_CSS % {"w": CANVAS_WIDTH}
    if mode == "center":
        return css, "", True
    return css, f"<script>{FIT_JS % {'w': CANVAS_WIDTH}}</script>", True


def build(accent: str | None, out_path: str, fit: str = "width",
          mode: str = "prototype") -> str:
    renderer = Renderer(DESIGN_DIR, accent)
    helmet, body = renderer.render(ENTRY[: -len(".dc.html")])

    mode_css, mode_js = "", ""
    if mode == "prototype":
        root_open, screens = build_screens(renderer, body)
        body = f"{root_open}\n{screens}\n</div>"
        mode_css = PROTOTYPE_CSS.strip()
        mode_js = f"<script>{ROUTER_JS % {'nav': json.dumps(NAV)}}</script>"

    body, hover_css = lift_hover_styles(body)
    fit_css, fit_js, wrap = fit_layer(fit)
    if wrap:
        body = f'<div id="dc-canvas">\n{body}\n</div>'

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(PAGE_TITLE)}</title>
<!-- Generated by build.py from design/{html.escape(ENTRY)} — edit the .dc.html, not this file. -->
{clean_helmet(helmet)}
<style>
{fit_css.strip()}
{mode_css}
{hover_css}
</style>
</head>
<body>
{body}
{mode_js}
{fit_js}
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return page


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default=os.path.join(HERE, "index.html"),
                    help="output file (default: index.html)")
    ap.add_argument("--accent", help="override the accent prop, e.g. '#3B6FE0'")
    ap.add_argument("--fit", choices=("width", "center", "none"), default="width",
                    help="width: scale the canvas to span the window (default); "
                         "center: leave it at 1:1, centred; none: raw canvas")
    ap.add_argument("--mode", choices=("prototype", "canvas"), default="prototype",
                    help="prototype: clickable, login -> dashboard -> menu (default); "
                         "canvas: every screen stacked on one page, with captions")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    page = build(args.accent, args.out, args.fit, args.mode)
    print(f"wrote {args.out} ({len(page):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
