# Atlas Console — OrgMS UI mockups

Static implementation of the **Atlas Console** canvas from the Claude Design project
*UI mockups for local system*
(`822519ab-3e4c-4d32-b405-89638c8b2da9`).

Desktop screens at 1440px, delivered two ways: a **clickable prototype**
(`index.html`) and the **full canvas** with every screen stacked and captioned
(`canvas.html`).

## The prototype flow

`index.html` opens on Login. **Sign in** goes to the Dashboard; from there every
item in the sidebar is live, and the `admin / Superuser` row at the bottom of
the sidebar signs back out to Login. Each screen gets a URL hash
(`index.html#customers`), so the browser's back button and deep links work.

| Menu item | Screen |
|-----------|--------|
| Dashboard | 4 KPI tiles, recent sales, recent expenses, top products |
| Customers | list + profile with orders tab + record-payment modal |
| Inventory | stock list + stock-movement timeline |
| Suppliers | purchase history + payments against a purchase |
| Expenses | placeholder — see below |
| Sales | list + new-sale form + printable invoice |
| Submit Bill | bill-claim form |
| My Bills | the submitter's own claims |
| Review Bills | approval queue with pending/approved/rejected totals |
| Reports | expense breakdown, payment stats, credit/debit ledger |
| Settings | accent picker, appearance mode, live preview |

**Expenses has no artboard** in this design round — expenses only appear on the
Dashboard and in Reports. Rather than leave a dead menu item, that screen shows
a short card saying so. Design it and it drops into the same slot.

Submit Bill and My Bills were drawn as loose panels under the Review Bills
artboard; the build wraps each in the standard app frame with its own sidebar so
each menu item lands on a real screen.

## Files

```
index.html                    clickable prototype — open it in a browser
canvas.html                   all screens stacked on one page, with captions
build.py                      compiler: design/*.dc.html -> html
design/Atlas Console.dc.html  source canvas (markup + data), from Claude Design
design/Sidebar.dc.html        sidebar component the canvas imports 8×
design/support.js             Claude Design canvas runtime (only used by the .dc.html sources)
```

Both outputs are standalone — no runtime, no build step at view time. The only
network request is the Google Fonts stylesheet (Plus Jakarta Sans + IBM Plex
Mono); without it the page falls back to system sans / monospace and still reads
fine. The prototype's routing is ~30 lines of inline JS.

## Fitting the window

The artboards are drawn at a fixed 1440px (plus 56px gutters = a 1552px canvas),
so on a wide monitor they would otherwise sit against the left edge with dead
space beside them. A small inline script scales the whole canvas to span the
window — up on wide screens, down on narrow ones — so it always fills the
viewport and never scrolls sideways. It re-runs on resize.

    python3 build.py --fit width    # scale to fill (default)
    python3 build.py --fit center   # leave at 1:1, centred, gutters either side
    python3 build.py --fit none     # raw canvas, top-left, no wrapper

With JavaScript off, `--fit width` still degrades to a centred 1:1 canvas.

## Editing

`design/*.dc.html` is the source of truth. Edit markup or the data in the
`renderVals()` block at the bottom of each file, then rebuild:

```bash
python3 build.py                             # prototype  -> index.html
python3 build.py --mode canvas -o canvas.html  # stacked canvas
python3 build.py --accent '#3B6FE0'          # recolour the accent prop
python3 build.py --fit center                # see "Fitting the window" above
```

Rebuild **both** files after editing a screen, or `canvas.html` will drift.

`build.py` needs `python3` and `node` (node evaluates the components' real
`renderVals()`, so the data never has to be duplicated in Python).

It expands the design-canvas directives into plain HTML:

- `{{ expr }}` — value from `renderVals()`, or the current `sc-for` scope
- `<sc-for list="{{ xs }}" as="x">` — repeat, one pass per item
- `<sc-if value="{{ cond }}">` — keep the block when truthy
- `<dc-import name="Sidebar" active="Sales">` — inline another component with props
- `style-hover="…"` — lifted into a generated `.dc-hN:hover { … }` rule
- `<helmet>` — moved into `<head>`; the canvas-editor-only thumbnail and
  `design_doc_mode` meta are dropped

In prototype mode it then splits the canvas into screens and drops the page
header and the per-section captions. `design/Sidebar.dc.html` carries two local
additions the router keys off: `data-nav="{{ it.label }}"` on each nav link and
`data-signout="1"` on the account row. They change nothing about how it renders.

## Data

The mockups use the records already in the live instance — customer Rabby
(Penta Global Limited), supplier Habib Rahman, items Clip and Chiruni — so the
numbers on screen match what the client will recognise. Amounts are in BDT and
set in IBM Plex Mono so columns align.
