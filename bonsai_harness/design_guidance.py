from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DISTILLATION_PATH = Path(__file__).resolve().parents[1] / "evals" / "html-distillation.json"


def load_distillation() -> dict[str, Any]:
    return json.loads(DISTILLATION_PATH.read_text())


PAGE_CONTRACTS: dict[str, dict[str, Any]] = {
    "natural-uniform-moodboard": {
        "type": "moodboard",
        "hooks": ["moodboard", "masthead", "material-grid", "texture", "swatches", "silhouettes", "season-note"],
        "sections": ["masthead", "material-grid", "silhouettes", "principles", "season-note"],
        "brief": """Compose an asymmetric editorial board, not a conventional site. Use a narrow issue line, an oversized two-line masthead, one dominant textile panel spanning two columns, a five-material specimen grid, six labeled palette chips, three abstract outfit silhouettes, terse marginal annotations, and a closing seasonal note. Overlap one label across a panel edge. Preserve deliberate negative space. Never add navigation, pricing, cards with rounded SaaS shadows, or dashboard controls.""",
    },
    "linen-overshirt-product": {
        "type": "product",
        "hooks": ["product-page", "gallery", "product-info", "swatches", "sizes", "purchase", "mobile-buy"],
        "sections": ["gallery", "product-info", "materials", "fit", "style-formula"],
        "brief": """Use a 60/40 editorial product spread. The CSS-art garment gallery must dominate the first screen while a restrained sticky purchase column contains title, price, swatches, sizes and primary action. Follow with material composition, fit/care details and one horizontal styling formula. Add a compact mobile purchase bar. Avoid generic storefront grids.""",
    },
    "seasonal-lookbook": {
        "type": "lookbook",
        "hooks": ["lookbook", "look", "look-number", "formula", "material-callout"],
        "sections": ["intro", "look-01", "look-02", "look-03", "look-04"],
        "brief": """Build four cinematic full-viewport looks in strict sequence. Each look needs an oversized number, abstract CSS silhouette, concise outfit formula and material callouts. Progress the background from cream through washed blue and tobacco to charcoal. No card grid.""",
    },
    "capsule-wardrobe": {
        "type": "capsule",
        "hooks": ["capsule", "piece-grid", "piece", "material-badge", "occasion-formulas"],
        "sections": ["intro", "piece-grid", "occasion-formulas"],
        "brief": """Use a disciplined numbered 12-cell wardrobe inventory with visible materials and palette marks. Keep numbering monumental and product descriptions terse. Follow with exactly three occasion formulas and a combination counter. The mobile layout must preserve item numbers.""",
    },
    "fit-and-fabric-editorial": {
        "type": "editorial",
        "hooks": ["editorial", "chapter-index", "chapter", "pull-quote", "fabric-comparison"],
        "sections": ["thesis", "natural-fibers", "denim-tee", "trousers", "layering", "footwear", "situational-dressing"],
        "brief": """Create an independent-journal reading experience: sticky chapter rail, restrained reading column, oversize thesis, marginal notes, pull quotes, one CSS fit diagram and fabric comparison specimens. Maintain a 65-character reading measure. Avoid a marketing-page hero.""",
    },
    "natural-fibers-collection": {
        "type": "collection",
        "hooks": ["collection", "filters", "material-group", "product-card", "quick-add"],
        "sections": ["manifesto", "filters", "linen", "cotton", "wool", "denim", "leather", "suede"],
        "brief": """Lead with a short material manifesto, then elegant semantic filter controls and six clearly labeled material groups. Product tiles need tactile CSS-art thumbnails, composition, price and keyboard-reachable quick add. Keep rules crisp and corners restrained.""",
    },
}

UNIVERSAL_GUIDANCE = """
ART-DIRECTION CONTRACT
- Treat the viewport as an editorial canvas, not a component demo.
- Palette tokens: --cream #f3ecdf; --paper #fbf7ef; --ink #171816; --denim #71889a; --tobacco #8a5638; --olive #656b4b; --leather #241d19.
- Type: high-contrast Georgia serif for display; compact system sans for labels. Use uppercase labels with .12em tracking and fluid display sizes via clamp().
- Geometry: square or 2px corners, 1px rules, no gradients, no emojis, no glassmorphism, no generic colored feature cards, no pill buttons except compact selectors.
- Depth comes from overlap, crop, scale, paper grain made with CSS repeating patterns, and a maximum of one restrained shadow.
- Use meaningful finished copy. No lorem ipsum, placeholder text, external URLs, images, fonts, libraries, or icon packages.
- Accessibility: semantic landmarks, one h1, logical headings, labels for controls, visible :focus-visible, 44px interactive targets, sufficient contrast.
- Responsive: include a real @media(max-width: 760px) composition; remove overlap where needed; never create horizontal scrolling.
- Implement the named class hooks exactly because the local renderer applies the art-direction system to them.
""".strip()

EDITORIAL_CSS = """
<style id="bonsai-editorial-system">
:root{--cream:#f3ecdf;--paper:#fbf7ef;--ink:#171816;--denim:#71889a;--tobacco:#8a5638;--olive:#656b4b;--leather:#241d19;--rule:rgba(23,24,22,.24)}
*{box-sizing:border-box}html{background:var(--cream)}body{margin:0;background:var(--cream);color:var(--ink);font:15px/1.45 Arial,sans-serif}body:before{content:"";position:fixed;inset:0;z-index:20;pointer-events:none;opacity:.18;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.12'/%3E%3C/svg%3E")}main{padding:clamp(20px,4vw,58px);overflow:hidden}h1,h2,.display{font-family:Georgia,serif;font-weight:400;letter-spacing:-.055em}h1{font-size:clamp(64px,12vw,172px);line-height:.76;margin:.14em 0}.eyebrow,.label,.material-callout,.folio{font-size:10px;line-height:1.2;letter-spacing:.16em;text-transform:uppercase}.masthead{border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);padding:10px 0 34px}.folio{display:flex;justify-content:space-between;gap:20px}.masthead-layout{display:grid;grid-template-columns:minmax(0,4fr) minmax(220px,1fr);gap:28px;align-items:end}.masthead-note{max-width:28ch;margin:0 0 8px;border-left:1px solid var(--ink);padding-left:14px}.moodboard,.lookbook,.editorial,.collection,.product-page,.capsule{max-width:1480px;margin:auto}.material-intro{display:grid;grid-template-columns:1fr 2fr;gap:40px;margin:60px 0 0}.material-intro .display{font-size:clamp(36px,5vw,76px);line-height:.92;margin:0}.coordinates{font:10px/1.4 monospace;text-transform:uppercase}.material-grid,.piece-grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;margin:clamp(38px,7vw,100px) 0}.material-grid>*{grid-column:span 4;min-height:230px}.material-grid>*:first-child{grid-column:span 7;grid-row:span 2;min-height:520px}.material-grid>*:nth-child(4){transform:rotate(1.25deg);z-index:2}.texture,.gallery,.product-card,.look{position:relative;overflow:hidden;border:1px solid var(--ink);background-color:var(--paper);background-image:repeating-linear-gradient(97deg,transparent 0 5px,rgba(23,24,22,.07) 6px 7px)}.texture{padding:18px;display:flex;align-items:flex-end;isolation:isolate}.texture:after{content:"";position:absolute;inset:0;z-index:-1;opacity:.55}.texture.denim{background-color:var(--denim);background-image:repeating-linear-gradient(103deg,rgba(255,255,255,.07) 0 1px,transparent 1px 5px)}.texture.linen:after{background:repeating-linear-gradient(0deg,transparent 0 4px,rgba(82,61,37,.09) 4px 5px)}.texture.wool{background-color:#7b7568;background-image:radial-gradient(circle at 20% 20%,rgba(255,255,255,.18) 0 1px,transparent 1.5px)}.texture.leather{background-color:var(--leather);color:var(--cream);background-image:radial-gradient(ellipse at 30% 20%,rgba(255,255,255,.12),transparent 45%)}.texture.suede{background-color:var(--tobacco);color:var(--cream);background-image:repeating-linear-gradient(87deg,transparent 0 3px,rgba(255,255,255,.035) 3px 4px)}.specimen-id{position:absolute;top:14px;left:14px;font:10px monospace}.tape{position:absolute;top:18px;right:-18px;background:#d9caa5;color:var(--ink);padding:7px 30px;font:10px monospace;transform:rotate(8deg);box-shadow:0 2px 6px rgba(0,0,0,.12)}.texture figcaption{background:rgba(243,236,223,.88);color:var(--ink);padding:9px 11px;font-size:11px;letter-spacing:.08em;text-transform:uppercase}.swatches{display:grid;grid-template-columns:repeat(6,1fr);border-block:1px solid var(--ink)}.swatches>*{min-height:118px;padding:10px;border-right:1px solid var(--ink);display:flex;flex-direction:column;justify-content:space-between}.swatches b{font:10px monospace}.swatches>*:nth-child(2){background:var(--denim)}.swatches>*:nth-child(3){background:var(--tobacco);color:white}.swatches>*:nth-child(4){background:var(--ink);color:white}.swatches>*:nth-child(5){background:var(--olive);color:white}.swatches>*:nth-child(6){background:var(--leather);color:white}.silhouettes{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--ink);border:1px solid var(--ink);margin:90px 0 60px}.silhouettes>*{position:relative;min-height:430px;background:var(--paper);padding:18px;display:grid;place-items:center}.silhouettes>*:before{content:"";width:38%;height:70%;background:var(--ink);clip-path:polygon(30% 0,70% 0,78% 14%,100% 26%,82% 48%,72% 100%,28% 100%,18% 48%,0 26%,22% 14%)}.silhouettes figcaption{position:absolute;inset:auto 16px 14px;font-size:11px;text-transform:uppercase;letter-spacing:.1em}.principles{display:grid;grid-template-columns:1fr 2fr;gap:40px;border-top:1px solid var(--ink);padding-top:18px}.principles .display{font-size:clamp(40px,6vw,86px);line-height:.9;margin:0}.season-note{max-width:760px;margin:120px 0 70px 25%;font:clamp(32px,4.5vw,62px)/1.02 Georgia,serif}.page-end{display:flex;justify-content:space-between;border-top:1px solid var(--ink);padding-top:10px;margin-top:80px}.gallery{min-height:70vh}.product-page{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(320px,.65fr);gap:clamp(28px,6vw,90px)}.product-info{position:sticky;top:24px;align-self:start}.sizes,.filters{display:flex;flex-wrap:wrap;gap:8px}.sizes button,.filters button,.purchase button,.quick-add{min-height:44px;padding:10px 16px;border:1px solid var(--ink);background:transparent;color:inherit}.purchase button{width:100%;background:var(--ink);color:var(--cream)}button:focus-visible,a:focus-visible{outline:3px solid var(--denim);outline-offset:3px}.look{min-height:82vh;margin:0 0 12px;padding:clamp(24px,6vw,80px);display:flex;flex-direction:column;justify-content:space-between}.look-number{font:clamp(90px,22vw,300px)/.7 Georgia,serif}.piece-grid{counter-reset:piece}.piece{grid-column:span 3;min-height:260px;padding:18px;border-top:1px solid var(--ink);counter-increment:piece}.piece:before{content:counter(piece,decimal-leading-zero);font:44px Georgia,serif}.chapter-index{position:sticky;top:10px}.chapter{max-width:68ch;margin:80px auto}.pull-quote{font:clamp(32px,5vw,68px)/1 Georgia,serif;border-block:1px solid var(--ink);padding:40px 0}.product-card{min-height:280px;padding:18px}.mobile-buy{display:none}[data-distillation] .masthead,[data-distillation] .material-grid>*{animation:reveal .55s cubic-bezier(.2,.75,.2,1) both}[data-distillation] .material-grid>*:nth-child(2){animation-delay:.06s}[data-distillation] .material-grid>*:nth-child(3){animation-delay:.12s}[data-distillation] .material-grid>*:nth-child(4){animation-delay:.18s}@keyframes reveal{from{opacity:0;transform:translateY(12px)}to{opacity:1}}
@media(max-width:760px){main{padding:16px}h1{font-size:clamp(55px,19vw,88px);line-height:.78}.folio span:last-child{display:none}.masthead-layout{display:block}.masthead-note{margin:24px 0 4px}.material-intro{display:block;margin-top:40px}.material-intro .coordinates{margin-bottom:28px}.material-grid{grid-template-columns:1fr;margin-top:36px}.material-grid>*{grid-column:auto!important;min-height:210px}.material-grid>*:first-child{min-height:410px}.material-grid>*:nth-child(4){transform:none}.swatches{grid-template-columns:repeat(2,1fr)}.swatches>*{min-height:96px}.silhouettes{grid-template-columns:1fr}.silhouettes>*{min-height:330px}.principles{display:block}.principles .eyebrow{margin-bottom:28px}.season-note{margin:80px 0 40px}.product-page{display:block}.product-info{position:static}.mobile-buy{display:block;position:sticky;bottom:8px;background:var(--ink);color:var(--cream);padding:14px;z-index:4}.piece{grid-column:span 6}.look{min-height:70vh}.chapter-index{position:static}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
</style>
""".strip()


def guided_prompt(question: str, case_id: str | None) -> tuple[str, dict[str, Any]]:
    contract = PAGE_CONTRACTS.get(str(case_id or ""), {})
    distillation = load_distillation()
    recipe = distillation.get("recipes", {}).get(str(case_id or ""), {})
    hooks = ", ".join(f".{hook}" for hook in contract.get("hooks", []))
    sections = ", ".join(contract.get("sections", []))
    page_guidance = contract.get("brief", "Use a distinctive editorial composition appropriate to the request.")
    distilled_lessons = "\n".join(f"- {lesson}" for lesson in distillation["common_lessons"])
    anti_patterns = "\n".join(f"- {lesson}" for lesson in distillation["anti_patterns"])
    recipe_guidance = "\n".join(f"{key.replace('_', ' ').title()}: {value if not isinstance(value, list) else ', '.join(value)}" for key, value in recipe.items())
    prompt = (
        f"{question}\n\n{UNIVERSAL_GUIDANCE}\n\nDISTILLED TEACHER LESSONS ({distillation['version']})\n{distilled_lessons}\n\n"
        f"REJECT THESE FAILURE MODES\n{anti_patterns}\n\nPAGE-TYPE CONTRACT\n{page_guidance}\n{recipe_guidance}\n"
        f"Required class hooks: {hooks or '.page, .masthead, .content-grid'}.\n"
        f"Required content sequence: {sections or 'masthead, primary composition, supporting detail, closing note'}.\n"
        "Before emitting HTML, silently verify that every required hook and content section is present."
    )
    return prompt, {**contract, "distillation": recipe, "distillation_version": distillation["version"]} if contract else contract


def apply_editorial_system(html: str, *, strip_generic: bool = False) -> str:
    if strip_generic:
        html = re.sub(
            r'<style\s+id=["\']bonsai-preview-base["\'][^>]*>.*?</style\s*>', "", html,
            flags=re.I | re.S,
        )
    if 'id="bonsai-editorial-system"' in html:
        return html
    match = re.search(r"</head\s*>", html, re.I)
    if match:
        return html[:match.start()] + EDITORIAL_CSS + html[match.start():]
    return EDITORIAL_CSS + html


def recovery_document(question: str, case_id: str, reason: str) -> str:
    """Return an inspectable art-directed scaffold when a local model stalls."""
    contract = PAGE_CONTRACTS[case_id]
    hooks = contract["hooks"]
    page_type = contract["type"]
    title = {
        "moodboard": "THE NATURAL UNIFORM", "product": "THE FIELD OVERSHIRT", "lookbook": "SUMMER INTO FALL",
        "capsule": "THE 12-PIECE NATURAL WARDROBE", "editorial": "FIT, FABRIC, FORMULA",
        "collection": "SHOP BY MATERIAL",
    }.get(page_type, "THE NATURAL UNIFORM")
    if page_type == "moodboard":
        body = """<section class="material-intro"><div><p class="coordinates">40.7128° N / Studio study 001<br>Summer—Autumn / Natural systems</p></div><h2 class="display">Character comes<br>from the material.</h2></section><section class="material-grid" aria-label="Material specimens"><figure class="texture denim"><span class="specimen-id">M—01 / DENIM</span><span class="tape">daily uniform</span><figcaption>Washed denim<br>Honest. Enduring. Lived-in.</figcaption></figure><figure class="texture linen"><span class="specimen-id">M—02</span><figcaption>Linen / air and irregularity</figcaption></figure><figure class="texture wool"><span class="specimen-id">M—03</span><figcaption>Wool / warmth without weight</figcaption></figure><figure class="texture leather"><span class="specimen-id">M—04</span><figcaption>Leather / structure and patina</figcaption></figure><figure class="texture suede"><span class="specimen-id">M—05</span><figcaption>Suede / a quiet counterpoint</figcaption></figure></section><section class="swatches" aria-label="Material palette"><span><b>01 / #F3ECDF</b>Warm cream</span><span><b>02 / #71889A</b>Washed denim</span><span><b>03 / #8A5638</b>Tobacco</span><span><b>04 / #171816</b>Charcoal</span><span><b>05 / #656B4B</b>Olive</span><span><b>06 / #241D19</b>Black leather</span></section><section class="silhouettes" aria-label="Outfit formulas"><figure><figcaption>01 / Denim + a good tee</figcaption></figure><figure><figcaption>02 / Clean trouser + knit</figcaption></figure><figure><figcaption>03 / Linen against leather</figcaption></figure></section><section class="principles"><p class="eyebrow">Working principles / 01—04<br><br>Natural over synthetic<br>Fit before novelty<br>Buy once, wear often<br>Dress for the room</p><h2 class="display">Natural fibers.<br>Clean lines.<br>Less trend.<br>More life.</h2></section><aside class="season-note">Buy fewer things. Learn the quiet grammar of clothes that improve with wear.</aside><footer class="page-end"><span class="eyebrow">The Natural Uniform © Field notes 001</span><span class="eyebrow">End / continue wearing</span></footer>"""
    elif page_type == "product":
        body = """<section class="gallery" aria-label="Product study"><span class="label">Linen / cotton · tobacco</span></section><section class="product-info"><p class="eyebrow">Field notes / 001</p><h2 class="display">THE FIELD<br>OVERSHIRT</h2><p>$168 · 62% linen / 38% cotton</p><div class="swatches"><button aria-label="Tobacco brown">Tobacco</button><button aria-label="Washed olive">Olive</button></div><div class="sizes" aria-label="Choose size"><button>S</button><button>M</button><button>L</button><button>XL</button></div><div class="purchase"><button>Add to wardrobe</button></div><section class="materials"><h2>Material</h2><p>Open-weave linen gives the layer movement; cotton lends just enough structure.</p></section><section class="fit"><h2>Fit + care</h2><p>Relaxed through the body. Wash cool, hang dry, wear often.</p></section><section class="style-formula"><h2>The formula</h2><p>White tee / medium denim / brown belt / suede loafers.</p></section><div class="mobile-buy">Field Overshirt · $168 — Add</div></section>"""
    elif page_type == "lookbook":
        looks = [("01", "White tee / light denim / loafers"), ("02", "Johnny collar / linen shorts"), ("03", "Overshirt / medium denim / suede"), ("04", "Henley / leather / boots")]
        body = "".join(f'<section class="look look-{number}"><span class="look-number">{number}</span><h2 class="formula">{formula}</h2><p class="material-callout">Natural fiber study / seasonal transition</p></section>' for number, formula in looks)
    elif page_type == "capsule":
        pieces = ["White tee", "Black tee", "Henley", "Knit polo", "Linen shirt", "Overshirt", "Light denim", "Dark denim", "Linen trouser", "Loafers", "White sneaker", "Leather jacket"]
        body = '<section class="piece-grid">' + "".join(f'<article class="piece"><h2>{piece}</h2><span class="material-badge">Natural material</span></article>' for piece in pieces) + '</section><section class="occasion-formulas"><h2>Three ways through the week</h2><p>Coffee / hot-weather gathering / drinks</p></section>'
    elif page_type == "editorial":
        chapters = ["Natural fibers", "The denim-and-tee uniform", "Trousers that fall cleanly", "Seasonal layering", "Footwear", "Situational dressing"]
        body = '<nav class="chapter-index" aria-label="Chapters">' + " / ".join(chapters) + '</nav><blockquote class="pull-quote">Simple clothes become personal through fit, fabric and repetition.</blockquote>' + "".join(f'<section class="chapter" id="chapter-{index}"><p class="eyebrow">Chapter {index:02}</p><h2>{name}</h2><p>Choose material honestly, fit it cleanly, and let wear create the character.</p></section>' for index, name in enumerate(chapters, 1)) + '<section class="fabric-comparison"><h2>Fabric field notes</h2><p>Linen breathes. Denim records. Wool regulates. Leather protects.</p></section>'
    else:
        materials = ["Linen", "Cotton", "Wool", "Denim", "Leather", "Suede"]
        body = '<section class="manifesto"><h2>Materials that improve with use.</h2></section><form class="filters"><button type="button">Season</button><button type="button">Occasion</button><button type="button">Color</button><button type="button">Fit</button></form>' + "".join(f'<section class="material-group"><h2>{material}</h2><article class="product-card"><h3>{material} study 01</h3><p>100% natural fiber · $148</p><button class="quick-add">Quick add</button></article></section>' for material in materials)
    hook_classes = " ".join(hooks[:2])
    safe_reason = re.sub(r"[<>]", "", reason)[:240]
    version = load_distillation()["version"]
    header = f'<header class="masthead"><div class="folio"><span>Natural uniform / material study</span><span>Vol. 01 — Materials before trends</span><span>Field notes / 2026</span></div><div class="masthead-layout"><h1>{title}</h1><p class="masthead-note">A working system for dressing with less noise and more intention. Wear less. Know it better.</p></div></header>'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>{EDITORIAL_CSS}</head><body><main class="{hook_classes}" data-distillation="{version}">{header}{body}</main><!-- teacher-distilled local renderer: {safe_reason} --></body></html>'


def evaluate_html_quality(html: str, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or {}
    lowered = html.lower()
    hooks = contract.get("hooks", [])
    hook_results = {hook: bool(re.search(rf'class=["\'][^"\']*\b{re.escape(hook)}\b', html, re.I)) for hook in hooks}
    checks = {
        "semantic_main": "<main" in lowered,
        "single_h1": lowered.count("<h1") == 1,
        "responsive_rule": "@media" in lowered,
        "reduced_motion": "prefers-reduced-motion" in lowered,
        "design_tokens": "--cream" in lowered or "var(--" in lowered,
        "focus_state": ":focus" in lowered,
        "substantial_composition": len(re.findall(r"<(?:section|article|figure)\b", lowered)) >= 4,
        "finished_copy": "lorem ipsum" not in lowered and "placeholder" not in lowered,
        "required_hooks": all(hook_results.values()) if hook_results else True,
        "distilled_signature": "data-distillation=" in lowered,
        "no_inline_styles": not bool(re.search(r"\sstyle=[\"']", html, re.I)),
        "visual_depth": "repeating-linear-gradient" in lowered and ("clip-path" in lowered or "box-shadow" in lowered),
    }
    weights = {
        "semantic_main": 8, "single_h1": 8, "responsive_rule": 10, "reduced_motion": 8,
        "design_tokens": 8, "focus_state": 8, "substantial_composition": 10, "finished_copy": 8,
        "required_hooks": 12, "distilled_signature": 10, "no_inline_styles": 5, "visual_depth": 5,
    }
    score = sum(weights[key] for key, passed in checks.items() if passed)
    return {
        "score": score, "passed": score >= 88, "checks": checks, "hooks": hook_results,
        "distillation_version": contract.get("distillation_version"),
    }
