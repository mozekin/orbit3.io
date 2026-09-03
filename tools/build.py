#!/usr/bin/env python3
"""Generator for the orbit3.io pages. Run from the repo root:  python3 tools/build.py
All page copy, titles, descriptions and schema live in this file; it writes the HTML files in place.
The site has no build step, so the generated HTML is what gets committed and served."""
import json, os, re, html

SITE = "https://orbit3.io"
CAL = "https://calendly.com/martin-orbit3/introductory-call"
LINKEDIN = "https://linkedin.com/company/orbit3"
GA = "G-YT6G7B299N"
TODAY = "2026-09-02"

# ---------------------------------------------------------------- icons
I = {
 "cal": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M4 9h16M8 3v4M16 3v4"/></svg>',
 "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
 "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" stroke-width="1.5"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/></svg>',
 "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/></svg>',
 "coins": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="9" cy="6" rx="6" ry="3"/><path d="M3 6v6c0 1.7 2.7 3 6 3s6-1.3 6-3V6"/><path d="M15 12.5c2.8.3 6 1.5 6 3.5 0 1.7-2.7 3-6 3-1.4 0-2.7-.2-3.7-.6"/></svg>',
 "robot": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="8" width="16" height="11" rx="3"/><path d="M12 8V4"/><circle cx="12" cy="3" r="1"/><path d="M9 13h.01M15 13h.01"/><path d="M9.5 16.5h5"/><path d="M1.5 12.5v2M22.5 12.5v2"/></svg>',
 "lock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="4.5" y="10" width="15" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><path d="M12 14v2"/></svg>',
 "cloud": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.2 9.1 4.5 4.5 0 0 0 7 18z"/></svg>',
 "server": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/></svg>',
 "chart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19h16"/><path d="M6 16v-5M11 16V7M16 16v-3M21 16V5"/></svg>',
 "rocket": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 15l4 4M14 4c3-1 5-1 6 0s1 3 0 6l-9 9-6-6 9-9z"/><path d="M9 12l3 3"/><circle cx="15" cy="9" r="1.5"/></svg>',
 "refresh": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/></svg>',
 "people": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.5a5 5 0 0 1 6 4.5"/></svg>',
 "eye": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
 "map": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z"/><path d="M9 4v14M15 6v14"/></svg>',
 "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M4 7l8 6 8-6"/></svg>',
 "linkedin": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05C20.4 8.65 21 11 21 14.1V21h-4v-6.1c0-1.45-.03-3.3-2-3.3-2 0-2.3 1.57-2.3 3.2V21H9z"/></svg>',
}

# ---------------------------------------------------------------- services registry
SERVICES = [
 ("cloudops-managed-services", "CloudOps Managed Services"),
 ("ai-solutions", "AI Solutions"),
 ("cloud-adoption", "Cloud Adoption"),
 ("cloud-security", "Cloud Security"),
 ("soc2-compliance", "SOC 2 Compliance"),
 ("cloud-optimisation", "Cloud Optimisation"),
 ("cloud-devops", "Cloud DevOps"),
 ("cloud-backup", "Cloud Backup"),
]
SURL = {s: f"/Services/{s}/" for s, _ in SERVICES}
SNAME = dict(SERVICES)

ORG = {
 "@type": "Organization", "@id": f"{SITE}/#organization", "name": "Orbit3", "url": f"{SITE}/",
 "logo": {"@type": "ImageObject", "url": f"{SITE}/images/logo.png", "width": 759, "height": 258},
 "image": f"{SITE}/images/og-image.png",
 "description": "Orbit3 is a managed cloud services and AI consultancy. We run cloud and IT operations for growing businesses and build custom AI and automation on top of them.",
 "email": "hello@orbit3.io",
 "sameAs": [LINKEDIN],
 "founder": {"@type": "Person", "name": "Martin", "jobTitle": "Founder", "url": f"{SITE}/about/"},
 "knowsAbout": ["Managed cloud services", "CloudOps", "FinOps", "Cloud security", "SOC 2 compliance", "SOC 2 remediation", "Vanta", "DevOps", "Cloud migration", "Backup and disaster recovery", "AI consulting", "LLM implementation", "Workflow automation", "Amazon Web Services", "Microsoft Azure", "Google Cloud"],
 "contactPoint": {"@type": "ContactPoint", "contactType": "sales", "email": "hello@orbit3.io", "url": CAL, "availableLanguage": "English"},
}

# ---------------------------------------------------------------- chrome
def nav_links(current):
    def a(href, label, extra=""):
        cur = ' aria-current="page"' if href == current else ""
        return f'<a href="{href}"{cur}{extra}>{label}</a>'
    dd = "".join(f'<a href="{SURL[s]}">{n}</a>' for s, n in SERVICES)
    svc_cur = ' aria-current="page"' if current.startswith("/Services/") else ""
    return f'''<nav class="nav-links" aria-label="Primary">
      {a("/", "Home")}
      <div class="dropdown">
        <a href="/Services/"{svc_cur}>Services</a>
        <div class="dropdown-menu">{dd}</div>
      </div>
      {a("/insights/", "Insights")}
      {a("/about/", "About")}
      {a("/contact/", "Contact")}
    </nav>'''

def header(current):
    dd = "".join(f'<a href="{SURL[s]}">{n}</a>' for s, n in SERVICES)
    return f'''<a class="skip" href="#main">Skip to content</a>
<input type="checkbox" id="navToggle" class="nav-toggle" hidden>
<header class="site-header">
  <div class="container nav">
    <a class="brand" href="/" aria-label="Orbit3 home"><img src="/images/logo-white.webp" alt="Orbit3" width="88" height="30"></a>
    {nav_links(current)}
    <div class="nav-cta">
      <a class="btn btn-primary" href="{CAL}" target="_blank" rel="noopener noreferrer">{I["cal"]} Book a call</a>
      <label for="navToggle" class="nav-burger" aria-label="Open menu" role="button" tabindex="0"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg></label>
    </div>
  </div>
</header>
<nav class="mobile-menu" aria-label="Mobile">
  <a href="/">Home</a>
  <a href="/Services/">Services</a>
  <div class="mm-label">Services</div>
  {dd}
  <div class="mm-label">&nbsp;</div>
  <a href="/insights/">Insights</a>
  <a href="/about/">About</a>
  <a href="/contact/">Contact</a>
  <a class="btn btn-primary" href="{CAL}" target="_blank" rel="noopener noreferrer">{I["cal"]} Book a call</a>
</nav>
<main id="main">'''

def footer():
    svc = "".join(f'<a href="{SURL[s]}">{n}</a>' for s, n in SERVICES)
    return f'''</main>
<footer class="footer">
  <div class="container">
    <div class="footer-top">
      <div class="footer-brand">
        <img src="/images/logo-white.webp" alt="Orbit3" width="88" height="30">
        <p>Managed cloud services and AI consulting. We run your cloud and IT operations and build the AI that moves your business forward.</p>
      </div>
      <div class="footer-col">
        <div class="footer-col-title">Services</div>
        {svc}
      </div>
      <div class="footer-col">
        <div class="footer-col-title">Company</div>
        <a href="/">Home</a>
        <a href="/Services/">All services</a>
        <a href="/insights/">Insights</a>
        <a href="/about/">About Orbit3</a>
        <a href="/contact/">Contact</a>
      </div>
      <div class="footer-col">
        <div class="footer-col-title">Get started</div>
        <a href="{CAL}" target="_blank" rel="noopener noreferrer">Book a free intro call</a>
        <a href="mailto:hello@orbit3.io">hello@orbit3.io</a>
        <div class="social" style="margin-top:14px">
          <a href="{LINKEDIN}" target="_blank" rel="noopener noreferrer" aria-label="Orbit3 on LinkedIn">{I["linkedin"]}</a>
          <a href="mailto:hello@orbit3.io" aria-label="Email Orbit3">{I["mail"]}</a>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <div>&copy;<span id="yr">2026</span> Orbit3. All rights reserved.</div>
      <div><a href="/sitemap.html">Sitemap</a> &nbsp;·&nbsp; <a href="/Services/">Services</a> &nbsp;·&nbsp; <a href="/contact/">Contact</a> &nbsp;·&nbsp; <button type="button" class="linklike" id="cookiePrefs">Cookie settings</button></div>
    </div>
  </div>
</footer>
<div class="consent" id="consent" hidden role="dialog" aria-label="Cookie consent" aria-live="polite">
  <p>We use Google Analytics to understand how the site is used. No analytics cookies are set unless you accept.</p>
  <div class="consent-actions"><button type="button" class="btn btn-primary" id="consentAccept">Accept</button><button type="button" class="btn btn-ghost" id="consentDecline">Decline</button></div>
</div>
<script>
document.getElementById('yr').textContent=new Date().getFullYear();
(function(){{
  var t=document.getElementById('navToggle');
  if(t){{document.querySelectorAll('.mobile-menu a').forEach(function(a){{a.addEventListener('click',function(){{t.checked=false;}});}});}}
  var els=document.querySelectorAll('.reveal');
  function showAll(){{els.forEach(function(el){{el.classList.add('is-visible');}});}}
  if('IntersectionObserver' in window){{
    var io=new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting){{e.target.classList.add('is-visible');io.unobserve(e.target);}}}});}},{{threshold:0.12}});
    els.forEach(function(el){{io.observe(el);}});
    setTimeout(showAll,1500);
  }} else {{ showAll(); }}
  var box=document.getElementById('consent'),KEY='o3-consent';
  function read(){{try{{return localStorage.getItem(KEY);}}catch(e){{return null;}}}}
  function write(v){{try{{localStorage.setItem(KEY,v);}}catch(e){{}}}}
  function apply(v){{if(v==='granted'&&window.gtag){{gtag('consent','update',{{analytics_storage:'granted'}});}}}}
  var saved=read(); if(saved){{apply(saved);}} else {{box.hidden=false;}}
  document.getElementById('consentAccept').addEventListener('click',function(){{write('granted');apply('granted');box.hidden=true;}});
  document.getElementById('consentDecline').addEventListener('click',function(){{write('denied');box.hidden=true;}});
  document.getElementById('cookiePrefs').addEventListener('click',function(){{box.hidden=false;}});
}})();
</script>
</body>
</html>
'''

def head(path, title, desc, ld_graph, robots="index, follow, max-image-preview:large"):
    url = SITE + path
    ld = json.dumps({"@context": "https://schema.org", "@graph": ld_graph}, ensure_ascii=False)
    t = html.escape(title, quote=True); d = html.escape(desc, quote=True)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{t}</title>
<meta name="description" content="{d}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{url}">
<meta name="robots" content="{robots}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Orbit3">
<meta property="og:locale" content="en_GB">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="{SITE}/images/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Orbit3: managed cloud services and AI consulting">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{SITE}/images/og-image.png">
<meta name="theme-color" content="#0a0d12">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/images/favicon-48.png" type="image/png" sizes="48x48">
<link rel="icon" href="/images/favicon-96.png" type="image/png" sizes="96x96">
<link rel="icon" href="/images/favicon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="/images/apple-touch-icon.png" sizes="180x180">
<link rel="preload" href="/fonts/dm-sans-variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/space-grotesk-variable.woff2" as="font" type="font/woff2" crossorigin>
<link href="/css/orbit3.css" rel="stylesheet">
<script>document.documentElement.classList.add('js');</script>
<script type="application/ld+json">{ld}</script>
<!-- Google tag (gtag.js) with Consent Mode v2: analytics cookies stay off until the visitor accepts -->
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
gtag('consent','default',{{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500}});
gtag('js',new Date());gtag('config','{GA}');</script>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
</head>
<body>
'''

def crumbs(items):
    """items: list of (name, url) with last being current page (url None)."""
    ld = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, **({"item": SITE + u} if u else {})} for i, (n, u) in enumerate(items)]}
    parts = [f'<a href="{u}">{n}</a>' if u else html.escape(n) for n, u in items]
    return ld, '<nav class="breadcrumb" aria-label="Breadcrumb">' + " / ".join(parts) + "</nav>"

def cta_buttons(primary="Book a free intro call"):
    return f'''<div class="hero-actions">
      <a class="btn btn-primary btn-lg" href="{CAL}" target="_blank" rel="noopener noreferrer">{I["cal"]} {primary}</a>
      <a class="btn btn-ghost btn-lg" href="/contact/">Send a message {I["arrow"]}</a>
    </div>'''

def cta_band(eyebrow, h2, p, primary="Book a free intro call"):
    return f'''<section class="section">
  <div class="container">
    <div class="cta-band reveal">
      <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
      <span class="eyebrow eyebrow--center">{eyebrow}</span>
      <h2 class="measure" style="margin-inline:auto">{h2}</h2>
      <p class="lede measure" style="margin-inline:auto">{p}</p>
      {cta_buttons(primary)}
    </div>
  </div>
</section>'''

def checklist(items):
    lis = "".join(f'<li>{I["check"]}<span><strong>{t}</strong>{d}</span></li>' for t, d in items)
    return f'<ul class="checklist">{lis}</ul>'

def faq_section(faqs):
    items = "".join(f'<details class="faq reveal"><summary><h3>{q}</h3></summary><div class="faq-a"><p>{a}</p></div></details>' for q, a in faqs)
    ld = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    return ld, f'''<section class="section section--alt" id="faq">
  <div class="container narrow">
    <span class="eyebrow">Questions we get asked</span>
    <h2>Frequently asked questions</h2>
    <div class="faq-list">{items}</div>
  </div>
</section>'''

def related(slugs, intro):
    cards = ""
    for s in slugs:
        cards += f'<a class="card card--link reveal" href="{SURL[s]}"><h3>{SNAME[s]}</h3><p>{BLURB[s]}</p><span class="link-arrow">Learn more {I["arrow"]}</span></a>'
    return f'''<section class="section">
  <div class="container">
    <div class="center measure" style="margin-bottom:40px"><span class="eyebrow eyebrow--center">Related services</span><h2>Often combined with this</h2><p>{intro}</p></div>
    <div class="grid grid-3">{cards}</div>
  </div>
</section>'''

def cards3(items, icon_default="cloud"):
    out = ""
    for it in items:
        icon = I[it.get("icon", icon_default)]
        out += f'<div class="card card--feature reveal"><span class="card-icon">{icon}</span><h3>{it["h"]}</h3><p>{it["p"]}</p></div>'
    return f'<div class="grid grid-3">{out}</div>'

def steps(items):
    return '<div class="steps reveal">' + "".join(f'<div class="step"><h3>{h}</h3><p>{p}</p></div>' for h, p in items) + "</div>"

def glance(rows):
    r = "".join(f'<div class="glance-row"><span>{k}</span><strong>{v}</strong></div>' for k, v in rows)
    return f'<div class="glass-panel glance"><div class="glance-head">At a glance</div>{r}</div>'

BLURB = {
 "cloudops-managed-services": "24/7 monitoring, patching, security and cost control for your AWS, Azure or Google Cloud environment, run by us.",
 "ai-solutions": "Custom LLM applications, RAG, workflow automation and AI agents, built on secure foundations and run as a managed service.",
 "cloud-adoption": "Assessment, architecture and migration for teams moving workloads to the cloud for the first time, or the second.",
 "cloud-security": "Security reviews, risk assessments and hardened target-state controls mapped to the standards you need to meet.",
 "soc2-compliance": "SOC 2 readiness and remediation in Vanta: we fix the failing tests, implement the controls and keep them green through the audit.",
 "cloud-optimisation": "FinOps analysis, right-sizing and governance that cut cloud spend and keep it down.",
 "cloud-devops": "CI/CD pipelines, infrastructure as code and observability so your team ships daily with confidence.",
 "cloud-backup": "Backup and disaster recovery designed around your recovery objectives, and tested so restores are routine.",
}

# ---------------------------------------------------------------- service page builder
def service_page(slug, title, desc, h1, lede, eyebrow, h2, intro_paras, bullets, panel, who, included, how_h2, how_steps, platforms, faqs, rel, cta, service_type, extra_sections=""):
    path = SURL[slug]
    crumb_ld, crumb_html = crumbs([("Home", "/"), ("Services", "/Services/"), (SNAME[slug], None)])
    faq_ld, faq_html = faq_section(faqs)
    svc_ld = {"@type": "Service", "@id": SITE + path + "#service", "name": SNAME[slug], "serviceType": service_type,
              "description": desc, "url": SITE + path, "provider": {"@id": f"{SITE}/#organization"},
              "areaServed": {"@type": "Place", "name": "Worldwide"},
              "offers": {"@type": "Offer", "url": CAL, "description": "Free 30-minute introductory call"}}
    paras = "".join(f"<p>{p}</p>" for p in intro_paras)
    inc = "".join(f'<li>{I["check"]}<span><strong>{t}</strong>{d}</span></li>' for t, d in included)
    plat = "".join(f'<div class="card reveal"><h3>{h}</h3><p>{p}</p></div>' for h, p in platforms)
    body = f'''<section class="page-hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    {crumb_html}
    <h1 class="measure">{h1}</h1>
    <p class="lede measure">{lede}</p>
    {cta_buttons()}
  </div>
</section>
<section class="section">
  <div class="container split">
    <div class="reveal">
      <span class="eyebrow">{eyebrow}</span>
      <h2>{h2}</h2>
      {paras}
      {checklist(bullets)}
    </div>
    <div class="order-first reveal">{panel}</div>
  </div>
</section>
<section class="section section--alt">
  <div class="container">
    <div class="center measure" style="margin-bottom:44px"><span class="eyebrow eyebrow--center">Who it's for</span><h2>{who["h2"]}</h2><p>{who["p"]}</p></div>
    {cards3(who["cards"])}
  </div>
</section>
<section class="section">
  <div class="container split" style="align-items:start">
    <div class="reveal">
      <span class="eyebrow">What's included</span>
      <h2>{included_h2(slug)}</h2>
      <p>{INCLUDED_INTRO[slug]}</p>
    </div>
    <ul class="checklist checklist--grid reveal">{inc}</ul>
  </div>
</section>
<section class="section section--alt">
  <div class="container split" style="align-items:start">
    <div class="reveal">
      <span class="eyebrow">How we deliver it</span>
      <h2>{how_h2}</h2>
      <p>{HOW_INTRO[slug]}</p>
    </div>
    {steps(how_steps)}
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="center measure" style="margin-bottom:40px"><span class="eyebrow eyebrow--center">Platforms</span><h2>AWS, Azure and Google Cloud</h2><p>{PLATFORM_INTRO[slug]}</p></div>
    <div class="grid grid-3">{plat}</div>
  </div>
</section>
{extra_sections}
{faq_html}
{related(rel, RELATED_INTRO[slug])}
{cta_band(cta["eyebrow"], cta["h2"], cta["p"], cta.get("btn", "Book a free intro call"))}
'''
    write(path, head(path, title, desc, [ORG, svc_ld, crumb_ld, faq_ld]) + header(path) + body + footer())

def included_h2(slug):
    return {
     "cloudops-managed-services": "Everything it takes to run a cloud environment well",
     "ai-solutions": "From scoping to a system your team relies on",
     "cloud-adoption": "A migration you can plan around",
     "cloud-security": "Controls you can show an auditor",
     "soc2-compliance": "Every failing test owned, fixed and evidenced",
     "cloud-optimisation": "Savings that survive next quarter",
     "cloud-devops": "The delivery platform your engineers wish they had",
     "cloud-backup": "Protection that has actually been restored from",
    }[slug]

INCLUDED_INTRO = {
 "cloudops-managed-services": "Managed services should mean you stop thinking about the plumbing. These are the things we take ownership of, with the scope and response targets written into a plain-English agreement before we start.",
 "ai-solutions": "AI work fails when it stops at the demo. We take a use case from a scoping conversation through a working build to a monitored production system, and we stay responsible for it.",
 "cloud-adoption": "Every migration we run is built around a written assessment, a target architecture you can question, and a cut-over plan with a way back.",
 "cloud-security": "Security work is only useful if it leaves you with controls that hold, evidence you can produce, and a team that knows what changed. This is what each engagement covers.",
 "soc2-compliance": "Vanta tells you what is failing. Someone still has to fix it, prove it, and keep it fixed through the observation window. That is the part we take ownership of.",
 "cloud-optimisation": "A one-off cost review saves money once. We combine the analysis with the governance and automation that stop waste creeping back.",
 "cloud-devops": "We build the pipeline, the infrastructure code and the observability together, because each one is weaker without the others.",
 "cloud-backup": "Backup is a process, not a product. We design it around what your business can afford to lose and how long it can afford to be down, then prove it works.",
}
HOW_INTRO = {
 "cloudops-managed-services": "Onboarding is where most managed-service relationships go wrong. Ours is deliberately structured so that by the end of the first month you know exactly what we're watching, what we'll fix without asking, and what we'll escalate.",
 "ai-solutions": "A clear, low-risk path from idea to value that compounds, rather than a one-off project that decays after launch.",
 "cloud-adoption": "Three phases, each with a deliverable you can review before we move to the next. No big-bang cut-overs.",
 "cloud-security": "We work from evidence, not assumptions: what is actually configured today, what the risk is, and what good looks like for your size and sector.",
 "soc2-compliance": "SOC 2 projects stall in remediation, not in the audit. We run remediation as an engineering project with an owner, a ranked backlog and a date.",
 "cloud-optimisation": "We start with the bill, not a tool. The first pass usually finds the obvious waste; the discipline afterwards is what keeps the number down.",
 "cloud-devops": "We meet your team where it is. Some clients want us to build the platform and hand it over; others want us to run it. Both start the same way.",
 "cloud-backup": "A backup you have never restored from is a hope, not a plan. Every engagement ends with a rehearsed recovery and a written runbook.",
}
PLATFORM_INTRO = {
 "cloudops-managed-services": "We run production environments on all three major clouds and the tooling around them. If you're multi-cloud or partly on-premises, that's normal for us.",
 "ai-solutions": "We build on the model and hosting options your data and compliance posture allow, from managed model APIs to private deployments inside your own cloud account.",
 "cloud-adoption": "We are not tied to one vendor. The target platform is a decision we make with you, based on your workloads, your team's skills and your commercial position.",
 "cloud-security": "Each platform has its own native security services and its own sharp edges. We work with the native tooling first and add third-party controls only where they earn their place.",
 "soc2-compliance": "Most of Vanta's infrastructure tests map to native platform services. Configured correctly and in code, they stay green without anyone touching them.",
 "cloud-optimisation": "Pricing models, commitment discounts and cost tooling differ by cloud. We know where the savings hide on each one.",
 "cloud-devops": "The principles are the same everywhere; the services differ. We work with the native pipelines and the platform-neutral tools your team already knows.",
 "cloud-backup": "Each cloud has native backup services that are excellent for some workloads and inadequate for others. We use them where they fit and add cross-region or cross-cloud protection where they don't.",
}
RELATED_INTRO = {
 "cloudops-managed-services": "Most managed-services clients start with one of these as a first project, or add them once the day-to-day is under control.",
 "ai-solutions": "AI systems are only as reliable as the platform under them. These are the services that make an AI build safe to depend on.",
 "cloud-adoption": "A migration is the moment to get the fundamentals right. These are the services most clients bundle with it.",
 "cloud-security": "Security is easier to maintain when someone is watching the environment every day. These services keep the posture from drifting.",
 "soc2-compliance": "SOC 2 controls are mostly good operations written down. These are the services that make the controls true rather than just documented.",
 "cloud-optimisation": "Cost, performance and reliability pull on each other. These services keep the balance once the savings are in.",
 "cloud-devops": "A good delivery platform needs a well-run environment underneath it. These services are the usual next step.",
 "cloud-backup": "Recovery planning sits alongside security and day-to-day operations. These services close the loop.",
}

# ---------------------------------------------------------------- file writer
def write(path, content):
    if path.endswith("/"):
        path += "index.html"
    fs = path.lstrip("/")
    os.makedirs(os.path.dirname(fs) or ".", exist_ok=True)
    with open(fs, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", fs, len(content))

def stub(old_path, new_path, name):
    """Meta-refresh stub for a URL that moved. GitHub Pages cannot send a 301, and Google treats an
    instant meta refresh as a permanent redirect."""
    target = SITE + new_path
    fs = old_path.lstrip("/")
    os.makedirs(os.path.dirname(fs) or ".", exist_ok=True)
    with open(fs, "w", encoding="utf-8") as f:
        f.write(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(name)} | Orbit3</title>
<link rel="canonical" href="{target}">
<meta http-equiv="refresh" content="0; url={target}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>location.replace("{target}");</script>
</head>
<body style="font-family:system-ui,sans-serif;background:#0a0d12;color:#eef2f6;padding:40px">
<p>This page has moved to <a href="{target}" style="color:#2dd4bf">{target}</a>.</p>
</body>
</html>
''')
    print("stub ", fs, "->", new_path)

# =====================================================================================
#  PAGE CONTENT
# =====================================================================================

# ---------- CloudOps Managed Services
service_page(
 slug="cloudops-managed-services",
 title="CloudOps Managed Services: 24/7 AWS, Azure & GCP | Orbit3",
 desc="Managed cloud services from Orbit3: 24/7 monitoring, patching, security, backup and cost control for AWS, Azure and Google Cloud, with one accountable team.",
 h1="CloudOps Managed Services <span class=\"text-gradient\">that never sleep</span>",
 lede="Your cloud environment, proactively monitored, secured, patched and cost-managed by us. One accountable partner instead of a rota of part-time attention.",
 eyebrow="Managed cloud services",
 h2="24/7 cloud management for AWS, Azure and Google Cloud",
 intro_paras=[
  "Most growing companies run their cloud the same way: one or two capable engineers look after it between feature work, alerts go to whoever is awake, and the monthly bill is a number nobody quite owns. It works until a certificate expires at 2am, a patch is missed, or the bill doubles without anyone noticing why.",
  "Orbit3's CloudOps Managed Services replace that arrangement with a team whose only job is to keep your environment secure, available and efficient. We act as an extension of your team, bringing certified cloud expertise to proactively manage, monitor and maintain your infrastructure, and we take ownership of the outcome rather than a ticket queue.",
 ],
 bullets=[
  ("Proactive 24/7 monitoring", "Alerting, triage and response across compute, data, networking and the services on top."),
  ("Security &amp; compliance built in", "Access management, patching, hardening and evidence you can hand to an auditor."),
  ("Cost optimisation (FinOps)", "Continuous right-sizing and commitment planning so the bill tracks real demand."),
  ("Backup &amp; disaster recovery", "Recovery objectives agreed, backups verified, restores rehearsed. See our <a href=\"/Services/cloud-backup/\">cloud backup service</a>."),
  ("One accountable partner", "A named engineer who knows your environment, not a call centre."),
 ],
 panel='''<div class="glass-panel" aria-hidden="true">
  <div style="padding:18px 18px 6px;display:flex;align-items:center;justify-content:space-between">
    <div style="font-family:var(--font-head);font-weight:600;color:#fff">Cloud health</div>
    <span class="pill"><span class="dot"></span> All systems operational</span>
  </div>
  <div style="padding:8px 18px 18px;display:grid;gap:10px">
    <div class="glance-row"><span>Production cluster</span><span class="pill"><span class="dot"></span>Healthy</span></div>
    <div class="glance-row"><span>Security &amp; patching</span><span class="pill"><span class="dot"></span>Up to date</span></div>
    <div class="glance-row"><span>Cloud spend vs. budget</span><strong style="color:var(--accent)">On track</strong></div>
    <div class="glance-row"><span>Backups verified</span><span class="pill"><span class="dot"></span>Today</span></div>
  </div>
</div>''',
 who={"h2": "Built for teams that have outgrown 'whoever is awake'",
      "p": "Managed cloud services make sense at a specific moment: when the cost of a bad night is higher than the cost of someone watching.",
      "cards": [
        {"icon": "people", "h": "Product companies with a small platform team", "p": "You have engineers who can run the cloud, but you'd rather they built the product. We take the operations load so they can."},
        {"icon": "shield", "h": "Businesses with compliance obligations", "p": "You need patching, access control and backups done consistently and evidenced, not done when someone remembers."},
        {"icon": "coins", "h": "Companies whose cloud bill has become a board topic", "p": "Spend has grown faster than revenue and nobody owns it. We put a number on the waste and then remove it."},
      ]},
 included=[
  ("Monitoring and alerting", "Metrics, logs and synthetic checks across your stack, with alert routing and on-call handled by us."),
  ("Incident response", "Triage, remediation and a written post-incident review for anything that affected service, within the response targets in your agreement."),
  ("Patch and lifecycle management", "Operating systems, managed services, runtimes and dependencies kept current on a schedule you approve."),
  ("Identity and access management", "Least-privilege roles, joiner and leaver processes, MFA enforcement and periodic access reviews."),
  ("Security posture management", "Native security tooling configured and reviewed, findings triaged and fixed, evidence retained for <a href=\"/Services/soc2-compliance/\">SOC 2</a> and ISO 27001 audits."),
  ("Backup and recovery operations", "Backup jobs monitored, restores tested on a schedule, recovery runbooks maintained."),
  ("Cost management (FinOps)", "Monthly cost review, anomaly detection, right-sizing and commitment recommendations you can act on."),
  ("Infrastructure as code", "Changes made through version-controlled Terraform or native templates, so every change is reviewable and repeatable."),
  ("Monthly service review", "A plain-English report on availability, incidents, security findings, spend and what we recommend next."),
 ],
 how_h2="Onboarding that leaves nothing implicit",
 how_steps=[
  ("Discover", "We inventory the environment, review access, identify single points of failure and agree the scope, priorities and response targets. You get a written findings report in the first two weeks whether or not you continue."),
  ("Stabilise", "We fix the urgent issues, put monitoring and backups in place, and bring patching and access up to a baseline. This is usually where the first cost savings appear too."),
  ("Run and improve", "Steady-state operations: monitoring, response, patching, reviews and a monthly conversation about what to improve next. Scope adjusts as your business does."),
 ],
 platforms=[
  ("Amazon Web Services", "Multi-account organisations, EKS and ECS workloads, RDS and Aurora, serverless estates and the IAM, Config, GuardDuty and Cost Explorer tooling that keep them honest."),
  ("Microsoft Azure", "Subscriptions and management groups, AKS, App Service, Azure SQL, Entra ID, Defender for Cloud and Azure Monitor, including hybrid estates with on-premises Active Directory."),
  ("Google Cloud", "Projects and folders, GKE, Cloud Run, Cloud SQL and BigQuery, with Security Command Center, Cloud Monitoring and billing exports for cost control."),
 ],
 faqs=[
  ("What does 'managed' actually cover?", "Everything needed to keep the environment secure, available and cost-efficient: monitoring, incident response, patching, access management, security posture, backup operations and cost management. We agree the exact scope and response targets in writing before we start, so there is no ambiguity about what we own."),
  ("Do we keep ownership of our cloud accounts?", "Yes. The accounts, data and infrastructure stay in your name and under your control. We work through delegated, least-privilege access that you can revoke at any time, and every change we make goes through version control."),
  ("How is it priced?", "As a fixed monthly fee scoped to your environment, agreed before we start. Project work such as a migration or a security remediation is quoted separately, so your operations fee stays predictable."),
  ("Can you work alongside our existing engineers?", "That is the most common arrangement. Your team keeps building; we take the operational load and share what we see. Many clients pair us with one internal engineer who acts as our day-to-day contact."),
  ("What if we are on more than one cloud, or partly on-premises?", "That is normal. We run environments that span AWS, Azure and Google Cloud, and hybrid estates with on-premises servers or a colocated data centre are within scope."),
  ("How quickly can you start?", "Discovery typically begins within a week of agreement. Most environments are at a stable baseline within the first month; complex estates take longer and we will tell you that up front."),
 ],
 rel=["cloud-security", "cloud-optimisation", "cloud-backup"],
 cta={"eyebrow": "Get started", "h2": "Ready to hand over the pager?", "p": "Book a free 30-minute call. We'll ask about your environment, tell you what we would look at first, and give you a straight answer on whether managed services are the right fit."},
 service_type="Managed cloud services",
)

# ---------- AI Solutions
service_page(
 slug="ai-solutions",
 title="AI Consulting & LLM Implementation Services | Orbit3",
 desc="AI consulting and implementation from Orbit3: custom LLM applications, RAG, workflow automation and AI agents, built on secure foundations and run for you.",
 h1="AI Solutions that ship <span class=\"text-gradient\">and keep working</span>",
 lede="We design, build and run custom AI for your business, from LLM-powered applications to workflow automation and AI agents, with the same managed-service rigour we bring to the cloud.",
 eyebrow="AI consulting and implementation",
 h2="Custom LLM applications, RAG and AI agents that reach production",
 intro_paras=[
  "Most AI projects stall between a promising demo and a system you can actually depend on. The demo answers questions from ten documents; production has to answer them from ten thousand, with the right permissions, without making things up, at a cost you can predict. Orbit3 closes that gap.",
  "We scope the right use case, build it on secure cloud foundations, integrate it with your existing tools and data, and then keep it running. Because we already run <a href=\"/Services/cloudops-managed-services/\">managed cloud operations</a> for our clients, your AI doesn't become another silo. It is monitored, secured and maintained as part of one accountable operation.",
 ],
 bullets=[
  ("Custom AI &amp; LLM applications", "Retrieval-augmented generation, copilots and assistants grounded in your own data."),
  ("Workflow automation &amp; agents", "Automations and agents that take real action across your systems, with human oversight built in."),
  ("Secure by design", "Your data stays in your cloud account, with access controls and audit trails from day one."),
  ("Run as a managed service", "Evaluation, monitoring, cost tracking and model updates handled after launch."),
 ],
 panel='''<div class="glass-panel" aria-hidden="true">
  <div style="padding:16px 18px;border-bottom:1px solid var(--border);font-family:var(--font-head);font-weight:600;color:#fff;display:flex;gap:8px;align-items:center"><span style="display:inline-flex;width:20px;color:var(--accent)">''' + I["robot"] + '''</span>Orbit3 AI Agent</div>
  <div style="padding:18px;display:grid;gap:12px">
    <div style="justify-self:end;max-width:78%;padding:11px 14px;background:var(--surface-2);border:1px solid var(--border);border-radius:14px 14px 4px 14px;color:var(--fg)">Summarise last week's support tickets and flag at-risk accounts.</div>
    <div style="justify-self:start;max-width:85%;padding:11px 14px;background:linear-gradient(180deg,rgba(45,212,191,.12),var(--surface));border:1px solid rgba(45,212,191,.28);border-radius:14px 14px 14px 4px;color:var(--fg)">Tickets processed and grouped by theme. Accounts showing churn signals have been flagged and routed to your CRM. Draft responses are queued for your review. <span style="color:var(--accent)">View &rarr;</span></div>
    <div style="display:flex;gap:8px;align-items:center;color:var(--fg-faint);font-size:.85rem"><span class="dot" style="width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent)"></span> Connected to Helpdesk · CRM · Cloud</div>
  </div>
</div>''',
 who={"h2": "For businesses that want AI doing work, not giving demos",
      "p": "The best AI use cases are rarely the most exciting ones. They are the repetitive, high-volume tasks where a reliable system pays for itself in weeks.",
      "cards": [
        {"icon": "people", "h": "Operations and support-heavy teams", "p": "Tickets, documents, emails and forms that follow patterns a well-built assistant can handle, with a person checking the edge cases."},
        {"icon": "chart", "h": "Companies sitting on unused knowledge", "p": "Policies, contracts, manuals and past work that nobody can search properly. A retrieval system turns that into answers your team trusts."},
        {"icon": "rocket", "h": "Product teams adding AI features", "p": "You want an AI capability inside your own product and need it built to production standards: evaluated, monitored, cost-controlled."},
      ]},
 included=[
  ("Use-case scoping", "A structured session to find the use case with the clearest payback and lowest risk, with a written recommendation either way."),
  ("Data and integration assessment", "Where the data lives, who may see it, what needs cleaning, and how the system will connect to your existing tools."),
  ("Retrieval-augmented generation (RAG)", "Document ingestion, chunking, embeddings, vector search and grounding so answers cite your sources rather than inventing them."),
  ("Custom assistants and copilots", "Interfaces inside the tools your team already uses, with role-based access to the underlying data."),
  ("AI agents and workflow automation", "Multi-step automations that read, decide and act across systems, with approval steps where the stakes require them."),
  ("Evaluation and guardrails", "Test sets, quality metrics, prompt-injection defences and output checks, run before launch and continuously after it."),
  ("Secure model hosting", "Managed model APIs or private deployments inside your own cloud account, chosen to match your data-handling obligations."),
  ("Monitoring and cost control", "Usage, latency, quality and spend tracked per feature, with alerts when any of them drift."),
  ("Ongoing improvement", "Model updates, prompt and retrieval tuning, and new capabilities added as a managed service rather than a new project each time."),
 ],
 how_h2="Scope. Build. Run.",
 how_steps=[
  ("Scope", "A short, free scoping call to find the use case with the clearest payback and the lowest risk. You leave with a recommendation, including 'don't do this yet' when that is the honest answer."),
  ("Build", "We design and ship a working solution on secure cloud foundations, integrated with your data and tools, and tested against real inputs with the people who will use it."),
  ("Run", "We monitor, secure and improve it as a managed service, so the value compounds instead of decaying after launch."),
 ],
 platforms=[
  ("Amazon Web Services", "Amazon Bedrock for managed model access, SageMaker for custom hosting, OpenSearch or Aurora for vector search, and Lambda and Step Functions for orchestration."),
  ("Microsoft Azure", "Azure OpenAI Service, Azure AI Search for retrieval, Azure Functions and Logic Apps for automation, with Entra ID controlling who can see what."),
  ("Google Cloud", "Vertex AI and Gemini models, Vertex AI Search, BigQuery for analytics-driven use cases, and Cloud Run for serving."),
 ],
 faqs=[
  ("Which AI models do you use?", "Whichever fits the use case, your data-handling obligations and your budget. That includes managed model APIs from the major providers and open-weight models deployed privately inside your own cloud account. We recommend, you decide, and we build so the model can be swapped later."),
  ("Will our data be used to train models?", "No. We build on services and deployment patterns where your data is not used for training, and we keep it inside your own cloud environment wherever possible. Access is controlled through your existing identity provider."),
  ("How do you stop the system making things up?", "By grounding answers in your own documents through retrieval, by testing against a set of known questions before launch, by constraining what the system may say when it is unsure, and by monitoring answer quality continuously afterwards."),
  ("How long does a first project take?", "A scoped first use case typically reaches a working, tested system in a matter of weeks rather than months. The scoping call is where we give you a realistic estimate for your situation."),
  ("Do we need a data science team?", "No. We handle the engineering. What we need from you is access to the people who do the work today, because they know which answers are right."),
  ("What happens after launch?", "The system is monitored, secured and improved as a managed service: model updates, prompt and retrieval tuning, cost tracking and new capabilities. You are not left holding a prototype."),
 ],
 rel=["cloudops-managed-services", "cloud-security", "cloud-devops"],
 cta={"eyebrow": "Get started", "h2": "Have an AI idea? Let's pressure-test it.", "p": "Book a free 30-minute scoping call. We'll tell you whether AI is the right tool, where it pays off first, and what it would take to ship.", "btn": "Book a free scoping call"},
 service_type="AI consulting and implementation",
)

# ---------- Cloud Adoption
service_page(
 slug="cloud-adoption",
 title="Cloud Migration & Adoption Consulting | Orbit3",
 desc="Cloud migration consulting from Orbit3: workload assessment, target architecture and a phased migration to AWS, Azure or Google Cloud with no big-bang cut-over.",
 h1="Move to the cloud <span class=\"text-gradient\">with confidence</span>",
 lede="A practical, purpose-built migration plan, assessed, designed and delivered by consultants who will still be around to run it afterwards.",
 eyebrow="Cloud migration and adoption",
 h2="A migration plan built around your workloads, not a template",
 intro_paras=[
  "Moving to the cloud is a sequence of decisions, and the expensive mistakes are made early: choosing a platform on a partner's recommendation rather than your workloads, lifting-and-shifting systems that should have been redesigned, or redesigning systems that should have been left alone.",
  "Orbit3's cloud adoption service starts with an honest assessment of what you run today and what it needs to do tomorrow. From that we design a target architecture you can question, and a phased migration with a way back at every step. Because we also provide <a href=\"/Services/cloudops-managed-services/\">managed cloud services</a>, we design environments we would be happy to operate.",
 ],
 bullets=[
  ("Workload assessment", "What you run, what it depends on, and what it costs today."),
  ("Target architecture", "A design built for your team's skills and your commercial position."),
  ("Phased migration", "Pilot first, then waves, with rollback planned for each."),
  ("Landing zone", "Accounts, identity, networking and guardrails set up properly from day one."),
 ],
 panel=glance([("Starts with", "Written assessment"), ("Cut-over style", "Phased, with rollback"), ("Platforms", "AWS · Azure · GCP"), ("Afterwards", "Optional managed run")]),
 who={"h2": "For teams making the move for the first time, or the second",
      "p": "Some clients are leaving a data centre or a hosting contract. Others moved years ago and inherited an environment that has never been tidied. Both are migrations.",
      "cards": [
        {"icon": "server", "h": "Leaving on-premises or a hosting provider", "p": "Hardware is ageing, a contract is ending, or the office server room is the last thing between you and remote working. You need a plan with dates."},
        {"icon": "refresh", "h": "Re-platforming an early cloud estate", "p": "The first migration was a lift-and-shift and the bill and the fragility show it. This time you want it designed."},
        {"icon": "rocket", "h": "Consolidating after growth or acquisition", "p": "Several environments, several ways of doing things. You want one landing zone, one identity model and one set of standards."},
      ]},
 included=[
  ("Discovery and dependency mapping", "An inventory of applications, data, integrations and the dependencies between them, so nothing is discovered on cut-over day."),
  ("Platform recommendation", "AWS, Azure or Google Cloud, chosen on your workloads, licensing, existing skills and commercial terms, with the reasoning written down."),
  ("Target architecture and landing zone", "Account structure, identity, networking, security guardrails and cost allocation designed before the first workload moves."),
  ("Migration strategy per workload", "Rehost, replatform, refactor, replace or retire, decided per system rather than for the whole estate at once."),
  ("Cost model", "A forecast of run costs on the target platform, compared with what you pay today, before you commit."),
  ("Pilot migration", "One representative workload moved end to end to prove the approach and the runbooks."),
  ("Wave planning and execution", "Remaining workloads grouped into waves with cut-over windows, testing plans and rollback steps for each."),
  ("Data migration", "Databases and file stores moved with integrity checks and minimal downtime, using native replication services where they fit."),
  ("Handover or managed run", "Documentation and training for your team, or a seamless transition to our managed service."),
 ],
 how_h2="Discover, design, migrate",
 how_steps=[
  ("Discovery", "A comprehensive assessment of your workloads and technology stack, including the dependencies and the costs. The output is a written report you own, with a recommended platform and approach."),
  ("Architecture", "A purpose-built target design and landing zone, reviewed with your team, with a cost forecast and a migration plan broken into waves."),
  ("Adoption", "A pilot workload first, then waves, each with its own testing and rollback plan. We finish with handover to your team or a transition into managed operations."),
 ],
 platforms=[
  ("Amazon Web Services", "Well-Architected reviews, AWS Organizations and Control Tower landing zones, Application Migration Service for rehosting and Database Migration Service for data."),
  ("Microsoft Azure", "Cloud Adoption Framework landing zones, Azure Migrate for assessment and rehosting, and hybrid identity with Entra ID for organisations that live in Microsoft 365."),
  ("Google Cloud", "Organisation and folder design, Migrate to Virtual Machines for rehosting, Database Migration Service, and GKE for teams heading towards containers."),
 ],
 faqs=[
  ("Which cloud should we choose?", "It depends on your workloads, your existing licensing, your team's skills and your commercial position. Microsoft-centric organisations often land well on Azure; product companies often favour AWS or Google Cloud. We give you a recommendation with the reasoning written down, and we are not paid by any vendor to steer you."),
  ("How long does a migration take?", "A small estate can move in weeks; a large one with legacy dependencies takes months. The discovery phase gives you a realistic plan with dates for each wave, and the pilot migration confirms it before you commit the rest."),
  ("Will there be downtime?", "Each workload gets its own cut-over plan with a defined window and a rollback. Many systems can move with minutes of downtime using replication; some need a maintenance window. We tell you which is which before the wave is scheduled."),
  ("Should we lift-and-shift or redesign?", "Usually both, decided per system. Rehosting gets you off ageing hardware quickly; redesigning pays off for the systems that cost the most to run or change. Doing either for everything is how migrations overrun."),
  ("What happens after the migration?", "Either we hand over with documentation and training, or the environment moves into our managed service. Because we designed it, there is no learning curve."),
  ("Can you help with cloud spend once we have moved?", "Yes. The cost model in the plan is the starting point, and our cloud optimisation service keeps the bill in line with the forecast."),
 ],
 rel=["cloudops-managed-services", "cloud-devops", "cloud-security"],
 cta={"eyebrow": "Get started", "h2": "Ready to move to the cloud?", "p": "Book a free 30-minute call and we'll outline a practical, low-risk path to the cloud tailored to your business."},
 service_type="Cloud migration consulting",
)

# ---------- Cloud Security
service_page(
 slug="cloud-security",
 title="Cloud Security Assessment & Compliance Services | Orbit3",
 desc="Cloud security services from Orbit3: configuration reviews, risk assessments, hardened controls and compliance mapping for AWS, Azure and Google Cloud.",
 h1="Cloud security <span class=\"text-gradient\">you can prove</span>",
 lede="We review your cloud security controls, run risk assessments, and build best-practice target-state controls that meet your compliance requirements and hold up under scrutiny.",
 eyebrow="Cloud security services",
 h2="Cloud security reviews, risk assessments and compliance controls",
 intro_paras=[
  "Cloud security problems rarely come from exotic attacks. They come from an over-permissive role created in a hurry, a storage bucket that was public for a week, a database that was never patched, or credentials in a repository. The platforms give you excellent tools to prevent all of that, and most environments have half of them switched off.",
  "Orbit3's cloud security service starts from what is actually configured today. We assess the environment against the platform's own best-practice frameworks and the standards you need to meet, prioritise the findings by real risk, then design and implement the target-state controls. If we also run your environment through <a href=\"/Services/cloudops-managed-services/\">managed services</a>, those controls are maintained and evidenced every month afterwards.",
 ],
 bullets=[
  ("Configuration and posture review", "Every account, role, network path and storage location, against a recognised benchmark."),
  ("Risk assessment", "Findings ranked by what an attacker could actually do with them, not by tool severity."),
  ("Target-state controls", "Identity, network, data protection, logging and detection designed and implemented."),
  ("Compliance mapping", "Controls mapped to ISO 27001, SOC 2, Cyber Essentials or the framework your customers ask about. Working towards SOC 2 in Vanta? See our <a href=\"/Services/soc2-compliance/\">SOC 2 remediation service</a>."),
 ],
 panel=glance([("Starts with", "Posture review"), ("Output", "Ranked findings + remediation plan"), ("Frameworks", "CIS · ISO 27001 · SOC 2 · Cyber Essentials"), ("Afterwards", "Controls maintained under managed services")]),
 who={"h2": "For businesses that have to answer a security questionnaire, or should",
      "p": "The trigger is usually external: a customer's due diligence, an insurer's questions, an audit date, or an incident somewhere similar.",
      "cards": [
        {"icon": "people", "h": "Vendors selling to larger customers", "p": "Enterprise procurement wants evidence of your controls. You need to be able to show them, not describe them."},
        {"icon": "shield", "h": "Regulated or certifying organisations", "p": "You are working towards ISO 27001, SOC 2 or Cyber Essentials and the cloud environment is the part nobody is sure about."},
        {"icon": "refresh", "h": "Teams that grew faster than their controls", "p": "Access was granted as needed and never reviewed. You would like to know what is actually exposed before someone else finds out."},
      ]},
 included=[
  ("Identity and access review", "Users, roles, service accounts and keys, with least-privilege recommendations and a clean-up plan."),
  ("Network and perimeter review", "Exposed services, security group and firewall rules, private connectivity and segmentation."),
  ("Data protection review", "Encryption at rest and in transit, key management, storage exposure and backup protection."),
  ("Logging, monitoring and detection", "Audit logs enabled and retained, threat detection services configured, alerts routed to someone who will act."),
  ("Benchmark assessment", "Configuration measured against CIS Benchmarks and the platform's own security best-practice framework."),
  ("Prioritised findings report", "Each finding with its real-world risk, the evidence behind it and the specific fix, ranked so you know what to do first."),
  ("Remediation", "We implement the fixes, or work alongside your team, with changes made through infrastructure as code where possible."),
  ("Compliance control mapping", "Findings and controls mapped to the framework you are working towards, with the evidence an auditor will ask for."),
  ("Re-assessment", "A follow-up review to confirm the fixes hold and to produce a clean baseline report."),
 ],
 how_h2="Assess, harden, comply",
 how_steps=[
  ("Assess", "We review controls across identity, network, data, logging and detection, using both automated benchmark tooling and manual inspection, and produce a risk-ranked findings report."),
  ("Harden", "We design the target-state controls and implement them, prioritising the fixes that remove the most risk for the least disruption."),
  ("Comply", "We map the controls to the standard your business must meet and package the evidence, then re-assess to confirm the environment holds."),
 ],
 platforms=[
  ("Amazon Web Services", "IAM Access Analyzer, Security Hub, GuardDuty, Config rules, CloudTrail and KMS, aligned to the AWS Foundational Security Best Practices and CIS Benchmarks."),
  ("Microsoft Azure", "Entra ID Conditional Access and Privileged Identity Management, Defender for Cloud, Azure Policy, Sentinel and Key Vault, aligned to the Microsoft cloud security benchmark."),
  ("Google Cloud", "Organisation policies, IAM Recommender, Security Command Center, VPC Service Controls, Cloud Audit Logs and Cloud KMS, aligned to the CIS Google Cloud Benchmark."),
 ],
 faqs=[
  ("Is this a penetration test?", "No. A penetration test tries to break in from the outside. A cloud security assessment reviews how the environment is configured from the inside, which is where most cloud breaches actually start. The two complement each other, and we can coordinate with a testing provider if you need both."),
  ("Will the assessment disrupt our environment?", "The review is read-only. Remediation involves changes, which we plan with you, make through version-controlled infrastructure code where possible, and schedule around your business."),
  ("Which compliance frameworks do you work with?", "Most commonly ISO 27001, SOC 2 and Cyber Essentials, plus the platform benchmarks from CIS and the cloud providers themselves. If your customers ask about a specific framework, we map to that."),
  ("How long does an assessment take?", "A single-account environment can be assessed in days; a multi-account estate takes a few weeks. Remediation time depends on what we find and how much of it you want us to fix versus your own team."),
  ("Do you fix the problems or just report them?", "Both. The report is written so your team could act on it alone, and we are equally happy to implement the fixes ourselves. Most clients ask us to handle the high-risk items immediately and work through the rest together."),
  ("What keeps the environment secure afterwards?", "Controls drift as people and systems change. Our managed service maintains and evidences them every month; otherwise we recommend a re-assessment at least annually or after any major change."),
 ],
 rel=["soc2-compliance", "cloudops-managed-services", "cloud-backup"],
 cta={"eyebrow": "Get started", "h2": "Worried about your security posture?", "p": "Book a free 30-minute call and we'll help you find the gaps that matter most, and how to close them."},
 service_type="Cloud security assessment",
)

# ---------- Cloud Optimisation
service_page(
 slug="cloud-optimisation",
 title="Cloud Cost Optimisation & FinOps Services | Orbit3",
 desc="Cloud cost optimisation and FinOps from Orbit3: spend analysis, right-sizing, commitment planning and governance that cut your cloud bill and keep it down.",
 h1="Stop overpaying <span class=\"text-gradient\">for your cloud</span>",
 lede="Control public-cloud spend and get full transparency over costs, with inefficiencies corrected and the governance to stop them coming back baked into your pipeline.",
 eyebrow="Cloud cost optimisation",
 h2="Cut cloud spend without cutting performance",
 intro_paras=[
  "Cloud bills grow for predictable reasons: resources sized for a launch and never revisited, environments left running overnight, storage that is never tidied, data transfer nobody modelled, and on-demand pricing for workloads that have run steadily for two years. None of it is dramatic. All of it compounds.",
  "Orbit3's cloud optimisation service finds the waste, removes it, and then puts the tagging, budgets, alerts and automation in place so the savings last. We apply FinOps practice at a scale that suits a growing business: enough discipline to own the number, without a committee. For clients on our <a href=\"/Services/cloudops-managed-services/\">managed service</a>, cost review is part of every month.",
 ],
 bullets=[
  ("Spend analysis", "Where the money goes by service, team, environment and workload."),
  ("Right-sizing and clean-up", "Compute, databases, storage and idle resources aligned to real demand."),
  ("Commitment planning", "Reserved capacity and savings plans sized on actual usage, not optimism."),
  ("Governance that lasts", "Tagging, budgets, anomaly alerts and policy checks in the delivery pipeline."),
 ],
 panel=glance([("Starts with", "Your last three bills"), ("First output", "Ranked savings plan"), ("Levers", "Right-size · Schedule · Commit · Tidy"), ("Afterwards", "Budgets, alerts, monthly review")]),
 who={"h2": "For companies whose bill grew faster than their revenue",
      "p": "Optimisation pays off fastest where nobody has owned the bill. That describes most growing companies at some point.",
      "cards": [
        {"icon": "coins", "h": "Leadership asking why the bill doubled", "p": "The number has become a board question and the honest answer is 'we're not sure'. You need a breakdown and a plan."},
        {"icon": "chart", "h": "Product teams scaling infrastructure", "p": "Usage is growing, which is good, but unit costs are growing with it, which is not. You want margin to improve as you scale."},
        {"icon": "refresh", "h": "Estates that were migrated and never revisited", "p": "The lift-and-shift sized everything like the old servers. Two years on, the cloud is doing the same work at three times the price."},
      ]},
 included=[
  ("Cost and usage analysis", "Billing data broken down by service, account, environment and workload, with the trends and anomalies explained in plain English."),
  ("Tagging and cost allocation", "A tagging standard and enforcement so every pound can be attributed to a team, product or customer."),
  ("Right-sizing", "Compute instances, containers, databases and storage tiers matched to observed utilisation, with the evidence for each change."),
  ("Scheduling and idle clean-up", "Non-production environments shut down out of hours; orphaned volumes, snapshots, load balancers and addresses removed."),
  ("Commitment and discount planning", "Reserved instances, savings plans and committed-use discounts sized to your stable baseline, with the break-even shown."),
  ("Architecture recommendations", "Where a design change, such as serverless, spot capacity or a different storage class, would change the cost curve rather than trim it."),
  ("Budgets, alerts and anomaly detection", "Guardrails so an unexpected increase is a message on the day, not a surprise on the invoice."),
  ("Policy in the pipeline", "Cost checks and tagging rules enforced in infrastructure code and CI, so waste is caught before it is deployed."),
  ("Monthly review", "Spend against forecast, savings realised, new recommendations and a short conversation about what to do next."),
 ],
 how_h2="Analyse, right-size, sustain",
 how_steps=[
  ("Analyse", "We start with your billing data and utilisation metrics to surface where spend goes and where the waste hides, and produce a savings plan ranked by value and effort."),
  ("Right-size", "We correct the inefficiencies: resizing, scheduling, tidying and committing, each change evidenced and reversible."),
  ("Sustain", "We bake governance into your pipeline and processes, so savings last and new waste is caught early."),
 ],
 platforms=[
  ("Amazon Web Services", "Cost Explorer and Cost and Usage Reports, Compute Optimizer, Savings Plans and Reserved Instances, S3 storage classes and lifecycle policies, Budgets and Cost Anomaly Detection."),
  ("Microsoft Azure", "Cost Management and Advisor, Reservations and Savings Plans, Azure Hybrid Benefit for Windows and SQL licensing, storage tiering and budget alerts."),
  ("Google Cloud", "Billing exports to BigQuery, Recommender, committed-use discounts, sustained-use discounts, storage classes and budget alerts."),
 ],
 faqs=[
  ("How much can we realistically save?", "It depends entirely on how the environment was built and how long since anyone reviewed it. Estates that have never been optimised usually have significant waste; well-run ones less. The analysis phase puts a specific, evidenced number on it for your environment before you commit to any changes."),
  ("Will optimisation slow anything down?", "Not if it is done properly. Right-sizing is based on observed utilisation with headroom, changes are made one at a time with monitoring in place, and every change is reversible. Performance is a constraint, not a casualty."),
  ("Should we buy reserved capacity?", "Only for the part of your usage that is genuinely stable, and only once the environment has been right-sized, otherwise you lock in the waste. We size commitments on actual usage history and show the break-even before you buy."),
  ("Do we need a FinOps tool?", "Usually not to start. The cloud providers' native cost tools cover most needs for a growing business. We recommend third-party tooling only when the estate is large or multi-cloud enough to justify it."),
  ("How do you charge for this?", "As a scoped engagement for the analysis and remediation, and as part of the monthly fee for managed-service clients. We are transparent about the savings we expect before you commit."),
  ("How do we stop the bill creeping back up?", "Tagging, budgets, anomaly alerts and cost checks in the delivery pipeline, plus a monthly review. Waste creeps back when nobody is looking; the point of the governance is that someone always is."),
 ],
 rel=["cloudops-managed-services", "cloud-devops", "cloud-adoption"],
 cta={"eyebrow": "Get started", "h2": "Paying more for cloud than you should?", "p": "Book a free 30-minute call and we'll show you where the waste is hiding and what it would take to fix it."},
 service_type="Cloud cost optimisation and FinOps",
)

# ---------- Cloud DevOps
service_page(
 slug="cloud-devops",
 title="Cloud DevOps & CI/CD Consulting Services | Orbit3",
 desc="DevOps consulting from Orbit3: CI/CD pipelines, Terraform infrastructure as code, containers and observability so your team ships faster and more reliably.",
 h1="Ship faster, <span class=\"text-gradient\">more reliably</span>",
 lede="Automated, repeatable delivery pipelines and infrastructure as code that let your team release routinely, with quality and security built in from the start.",
 eyebrow="DevOps consulting",
 h2="Infrastructure as code and delivery pipelines that ship daily",
 intro_paras=[
  "The gap between a team that deploys every day and one that deploys every month is rarely talent. It is whether the environment is defined in code, whether tests and security checks run automatically, and whether anyone can see what happened when a release goes wrong. Those are engineering problems with known solutions.",
  "Orbit3 builds the delivery platform your team wishes it had: infrastructure as code, CI/CD pipelines, container platforms and observability, set up to your standards and handed over or run by us. It is the same tooling we use to operate client environments under <a href=\"/Services/cloudops-managed-services/\">managed services</a>, so it is built to be operated, not just demonstrated.",
 ],
 bullets=[
  ("CI/CD pipelines", "Build, test, scan and deploy on every change, with approvals where they matter."),
  ("Infrastructure as code", "Terraform or native templates for every environment, reviewed and versioned like application code."),
  ("Containers and orchestration", "Kubernetes, ECS or serverless, chosen for your workloads and your team's appetite to run them."),
  ("Observability", "Metrics, logs and traces that tell you what broke and why, before customers do."),
 ],
 panel=glance([("Starts with", "Delivery assessment"), ("Core tools", "Terraform · GitHub / GitLab · Kubernetes"), ("Built in", "Tests · Security scans · Observability"), ("Afterwards", "Handover or managed run")]),
 who={"h2": "For teams that want releases to be boring",
      "p": "Good DevOps is invisible: releases happen, environments match, and nobody is a single point of failure.",
      "cards": [
        {"icon": "rocket", "h": "Product teams releasing less often than they'd like", "p": "Deployments are manual, risky and scheduled for Friday nights. You want them to be a button, or nothing at all."},
        {"icon": "people", "h": "Companies where one person knows how it all works", "p": "Environments were built by hand and live in someone's head. You want them in code, reviewed and reproducible."},
        {"icon": "shield", "h": "Teams adding security and compliance to delivery", "p": "You need vulnerability scanning, policy checks and an audit trail without slowing engineers down."},
      ]},
 included=[
  ("Delivery assessment", "How code gets from a laptop to production today, where the delays and risks are, and a prioritised plan to fix them."),
  ("Infrastructure as code", "Environments defined in Terraform or native templates, structured into reusable modules with state management and review workflows."),
  ("CI/CD pipeline design and build", "Pipelines in GitHub Actions, GitLab CI, Azure DevOps or the platform-native service, with build, test, scan, artefact and deploy stages."),
  ("Environment strategy", "Consistent development, staging and production environments, created and destroyed on demand where that saves money."),
  ("Container platform", "Kubernetes (EKS, AKS, GKE), ECS or Cloud Run, with cluster configuration, ingress, autoscaling and upgrade processes."),
  ("Security in the pipeline", "Dependency and container scanning, secret detection, infrastructure policy checks and signed artefacts."),
  ("Observability", "Metrics, logs, traces and dashboards, with alerts tuned to what matters and runbooks for what fires."),
  ("Release practices", "Blue-green or canary deployments, feature flags and rollback procedures so releases are reversible."),
  ("Handover and enablement", "Documentation, pairing sessions and a runbook so your team owns the platform confidently, or a transition into managed operations."),
 ],
 how_h2="Automate, codify, observe",
 how_steps=[
  ("Automate", "We build the CI/CD pipelines that make releases routine: every change built, tested, scanned and deployed the same way, with approvals only where they add something."),
  ("Codify", "We put every environment into infrastructure as code so it is reproducible, reviewable and recoverable, and so the next environment takes an hour rather than a week."),
  ("Observe", "We add monitoring and feedback to delivery so the team sees the effect of every release, and so incidents are diagnosed from data rather than guesswork."),
 ],
 platforms=[
  ("Amazon Web Services", "EKS and ECS, CodePipeline and CodeBuild or GitHub Actions with OIDC, CloudFormation and CDK alongside Terraform, CloudWatch and X-Ray."),
  ("Microsoft Azure", "AKS and Container Apps, Azure DevOps Pipelines or GitHub Actions, Bicep alongside Terraform, Azure Monitor and Application Insights."),
  ("Google Cloud", "GKE and Cloud Run, Cloud Build or GitHub Actions with Workload Identity, Terraform, Cloud Monitoring, Logging and Trace."),
 ],
 faqs=[
  ("Do we need Kubernetes?", "Not necessarily. Kubernetes is the right answer for some workloads and an expensive distraction for others. We recommend the simplest platform that fits your applications and your team's capacity to operate it, which is often a managed container service or serverless."),
  ("Will this work with our existing repositories and tools?", "Yes. We build on GitHub, GitLab or Azure DevOps, whichever you use, and integrate with your existing test frameworks and ticketing. The aim is to improve your workflow, not replace it."),
  ("Which infrastructure-as-code tool do you use?", "Terraform by default, because it works across all three clouds and has the largest ecosystem. We also work with CloudFormation, CDK and Bicep where a team has already standardised on them."),
  ("How long does it take to see results?", "The first pipeline and the first environment in code usually land within the first few weeks. A full platform with containers, observability and security scanning takes longer, and we sequence it so the team benefits from each stage as it lands."),
  ("Can you run the platform for us afterwards?", "Yes. Many clients ask us to keep operating the platform under our managed service, so their engineers use it without having to maintain it. Others prefer a handover with documentation and training. Both are normal."),
  ("Does DevOps automation help with security and compliance?", "Substantially. Infrastructure in code gives you an audit trail for every change; scanning in the pipeline catches vulnerabilities before deployment; consistent environments remove the drift that causes most findings."),
 ],
 rel=["cloudops-managed-services", "cloud-adoption", "cloud-security"],
 cta={"eyebrow": "Get started", "h2": "Want to ship faster and safer?", "p": "Book a free 30-minute call and we'll map out how automated delivery could work for your team."},
 service_type="DevOps consulting",
)

# ---------- Cloud Backup
service_page(
 slug="cloud-backup",
 title="Cloud Backup & Disaster Recovery Services | Orbit3",
 desc="Cloud backup and disaster recovery from Orbit3: recovery objectives agreed, backups automated and isolated, restores tested and runbooks written.",
 h1="Recover quickly <span class=\"text-gradient\">when it matters</span>",
 lede="Resilient backup and disaster recovery that protects your business from data loss and downtime, designed around what you can afford to lose and tested so restores are routine.",
 eyebrow="Backup and disaster recovery",
 h2="Backup and disaster recovery you have actually tested",
 intro_paras=[
  "Every cloud provider offers backup. Very few businesses have checked that theirs works. The common failures are quiet: the backup job that has been failing for a month, the database that was never included, the backup stored in the same account as the ransomware, and the restore that takes three days when the business assumed three hours.",
  "Orbit3's cloud backup service starts with two numbers: how much data you can afford to lose and how long you can afford to be down. From those we design the backup and recovery approach, automate it, isolate it from the environment it protects, and rehearse the restore until it is routine. Under <a href=\"/Services/cloudops-managed-services/\">managed services</a>, the backups are monitored and test-restored on a schedule.",
 ],
 bullets=[
  ("Recovery objectives", "RPO and RTO agreed per system, so protection matches business impact."),
  ("Automated, isolated backups", "Immutable copies in a separate account or region, out of reach of a compromised environment."),
  ("Disaster recovery plan", "A written strategy and runbook for losing a region, an account or a system."),
  ("Tested restores", "Scheduled recovery tests, with the results recorded."),
 ],
 panel=glance([("Starts with", "RPO and RTO per system"), ("Protection", "Automated · Immutable · Isolated"), ("Proof", "Scheduled restore tests"), ("Afterwards", "Monitored under managed services")]),
 who={"h2": "For any business that would struggle to explain a lost week",
      "p": "The question is not whether you have backups. It is whether you have restored from them, and how long it took.",
      "cards": [
        {"icon": "shield", "h": "Businesses facing ransomware risk", "p": "Which is all of them. You need copies an attacker with your credentials cannot reach, and a plan for rebuilding from them."},
        {"icon": "people", "h": "Companies with contractual uptime obligations", "p": "Your customers or insurer want a documented, tested recovery plan with defined recovery times."},
        {"icon": "server", "h": "Teams relying on default cloud snapshots", "p": "Snapshots exist, in the same account, with no retention policy and no restore ever attempted. You would like more certainty than that."},
      ]},
 included=[
  ("Recovery objectives workshop", "Recovery point and recovery time objectives agreed per system with the people who depend on them, and written down."),
  ("Backup inventory and gap analysis", "What is protected today, what is not, and where existing backups would fail a real restore."),
  ("Backup design and automation", "Policies for databases, file storage, virtual machines, containers and configuration, using native services where they fit."),
  ("Immutable and isolated copies", "Backups that cannot be altered or deleted for a retention period, stored in a separate account or region from production."),
  ("Retention and cost control", "Retention schedules that meet your legal and business needs without paying to keep everything forever."),
  ("Disaster recovery strategy", "Backup-and-restore, pilot-light, warm standby or active-active, chosen per system by its recovery objectives and budget."),
  ("Recovery runbooks", "Step-by-step procedures for restoring each system, written so someone other than the author can follow them at 3am."),
  ("Restore testing", "Scheduled recovery tests, from single-file restores to full environment rebuilds, with timings and results recorded."),
  ("Monitoring and reporting", "Backup job monitoring, alerts on failure, and a periodic report showing coverage, test results and any gaps."),
 ],
 how_h2="Protect, plan, verify",
 how_steps=[
  ("Protect", "We agree recovery objectives, close the gaps in what is backed up, and automate resilient, isolated backups of every critical system."),
  ("Plan", "We design the disaster recovery strategy per system and write the runbooks, so recovery is a procedure rather than an improvisation."),
  ("Verify", "We rehearse restores on a schedule and record the results, so you know your recovery times are real and your backups are usable."),
 ],
 platforms=[
  ("Amazon Web Services", "AWS Backup with vault lock for immutability, cross-account and cross-region copies, RDS and Aurora point-in-time recovery, S3 versioning and Object Lock, and Elastic Disaster Recovery for warm standby."),
  ("Microsoft Azure", "Azure Backup with Recovery Services vaults and immutability, Azure Site Recovery for replication and failover, SQL point-in-time restore, and storage soft delete and versioning."),
  ("Google Cloud", "Backup and DR Service, persistent disk snapshot schedules, Cloud SQL automated backups with point-in-time recovery, and Cloud Storage retention policies and object versioning."),
 ],
 faqs=[
  ("What are RPO and RTO?", "Recovery point objective is how much data you can afford to lose, measured in time since the last backup. Recovery time objective is how long you can afford to be down. Every system gets its own pair, and they drive every design decision, because protecting everything to the highest standard is unaffordable and unnecessary."),
  ("Are cloud provider snapshots enough?", "Rarely on their own. Default snapshots usually live in the same account as production, have no retention policy, and have never been restored. They are a starting point, not a plan."),
  ("How do backups protect against ransomware?", "By being immutable and isolated. Immutable backups cannot be altered or deleted during their retention period, even by an administrator. Isolated backups live in a separate account or region with separate credentials, so an attacker who compromises production cannot reach them."),
  ("How often do you test restores?", "On a schedule agreed for each system, typically monthly for single-system restores and at least annually for a full disaster recovery rehearsal. Every test is timed and recorded so you can show the evidence."),
  ("What does disaster recovery cost?", "It scales with the recovery time you need. Backup-and-restore is inexpensive but slow; a warm standby costs more to run but recovers in minutes. The recovery objectives workshop is where we match each system to the cheapest option that meets its needs."),
  ("Can you take over backups for an environment we run ourselves?", "Yes. Backup and recovery can be delivered as a standalone engagement, with your team running the rest of the environment, or as part of our managed service."),
 ],
 rel=["cloudops-managed-services", "cloud-security", "cloud-optimisation"],
 cta={"eyebrow": "Get started", "h2": "Confident you could recover from data loss?", "p": "Book a free 30-minute call and we'll pressure-test your backup and recovery strategy."},
 service_type="Cloud backup and disaster recovery",
)


# ---------- SOC 2 Compliance & Remediation
service_page(
 slug="soc2-compliance",
 title="SOC 2 Remediation & Compliance Services (Vanta) | Orbit3",
 desc="SOC 2 remediation from Orbit3: we fix the failing tests in Vanta, implement the technical and organisational controls, and keep them green through the audit.",
 h1="SOC 2 compliance <span class=\"text-gradient\">without the scramble</span>",
 lede="Vanta shows you the gaps. We close them: cloud controls, policies, evidence and the operational discipline to stay audit-ready through the observation window and beyond.",
 eyebrow="SOC 2 remediation services",
 h2="SOC 2 readiness and remediation, delivered in Vanta",
 intro_paras=[
  "Most companies start SOC 2 the same way: a large customer asks for the report, you sign up to Vanta, connect your cloud accounts and identity provider, and a dashboard lights up with dozens of failing tests. The platform is doing its job. The problem is that every one of those tests is a piece of engineering or process work that someone now has to own, and your team already has a full-time job.",
  "Orbit3 takes ownership of the remediation. We work inside your Vanta workspace, rank the failing tests by audit risk and effort, fix the technical controls in your AWS, Azure or Google Cloud environment through infrastructure as code, run the organisational controls with you, and keep everything green through the observation window and the audit itself. If you are not on Vanta, the same approach works with Drata, Secureframe and similar platforms.",
 ],
 bullets=[
  ("Gap triage in Vanta", "Every failing test ranked by risk, effort and which Trust Services Criteria it affects."),
  ("Technical remediation", "MFA, logging, encryption, network exposure, patching, backups and change control fixed in code."),
  ("Organisational controls", "Policies, risk assessment, vendor reviews, access reviews and training run with you, not left in a template."),
  ("Audit-ready evidence", "Continuous, automated evidence in Vanta, plus the manual artefacts an auditor will still ask for."),
  ("Stay green after the audit", "Under <a href=\"/Services/cloudops-managed-services/\">managed services</a>, the controls are operated and monitored every month."),
 ],
 panel=glance([("Platform", "Vanta (also Drata, Secureframe)"), ("Scope", "Security criteria first, then Availability and Confidentiality if needed"), ("Typical path", "Gap triage → remediation → Type I → observation → Type II"), ("Afterwards", "Controls kept green under managed services")]),
 who={"h2": "For teams that bought Vanta and hit the wall of red",
      "p": "Compliance automation removes the spreadsheet. It does not remove the work. These are the situations we are usually called into.",
      "cards": [
        {"icon": "people", "h": "SaaS vendors with a deal waiting on the report", "p": "Procurement has asked for SOC 2 and the sales cycle is on hold. You need a credible readiness date and a team that can hit it."},
        {"icon": "shield", "h": "Startups with Vanta connected and nobody assigned", "p": "The integrations are live and the dashboard is red. Engineers are picking off tests between sprints, and the date keeps slipping."},
        {"icon": "refresh", "h": "Companies that passed Type I and drifted", "p": "The point-in-time report went fine. Six months later, tests are failing again and the Type II observation window is at risk."},
      ]},
 included=[
  ("Scoping and criteria selection", "Which systems are in scope, which Trust Services Criteria you need (Security is mandatory; Availability, Confidentiality, Processing Integrity and Privacy are optional), and what your customers actually asked for."),
  ("Vanta workspace review", "Integrations connected correctly, in-scope resources tagged, test ownership assigned, and the failing tests triaged into a ranked backlog."),
  ("Cloud control remediation", "Identity and MFA, audit logging, encryption at rest and in transit, network exposure, vulnerability management and patching, backup and recovery testing, fixed through Terraform or native templates so they do not drift."),
  ("Change management and SDLC controls", "Branch protection, peer review, CI checks, separation of environments and deployment approvals, evidenced automatically from your code host and pipeline."),
  ("Policy set", "Vanta's policy templates adapted to how your company actually operates, reviewed with you, approved and accepted by staff in the platform."),
  ("Risk assessment and vendor management", "A risk register that reflects your real business, and vendor reviews for the SaaS tools that hold your data."),
  ("People controls", "Onboarding and offboarding checklists, security awareness training, background checks where required, and quarterly access reviews set up as recurring tasks."),
  ("Evidence and auditor liaison", "Manual evidence collected and organised, auditor access to Vanta configured, and questions from the audit firm answered with your team."),
  ("Post-audit operations", "Monitoring of Vanta tests, recurring tasks completed on schedule and control drift fixed as part of managed services, so Type II renewals are routine."),
 ],
 how_h2="Triage, remediate, evidence, sustain",
 how_steps=[
  ("Triage", "We review the scope, the Vanta integrations and every failing test, and produce a ranked remediation plan with owners and a realistic readiness date. You get this whether or not you continue."),
  ("Remediate", "We fix the technical controls in your cloud environment through infrastructure as code and run the organisational controls with you: policies, risk assessment, vendor and access reviews, training."),
  ("Evidence and audit", "With the tests green, we collect the remaining manual evidence, set up auditor access and support your team through the Type I report and the Type II observation window."),
 ],
 platforms=[
  ("Amazon Web Services", "IAM and Identity Center for MFA and least privilege, CloudTrail and Config for audit logging and configuration history, GuardDuty and Security Hub for detection, KMS and default encryption, AWS Backup with tested restores. Vanta reads all of these directly."),
  ("Microsoft Azure", "Entra ID Conditional Access and Privileged Identity Management, Defender for Cloud, Azure Policy for enforced configuration, Monitor and Log Analytics for retained logs, Key Vault, and Azure Backup with recovery tests."),
  ("Google Cloud", "Organisation policies and IAM with enforced 2-step verification, Cloud Audit Logs with retention, Security Command Center, CMEK where required, and Backup and DR Service with scheduled restore tests."),
 ],
 faqs=[
  ("What is SOC 2 remediation?", "Remediation is the work between the gap assessment and the audit: fixing the technical controls (MFA, logging, encryption, network exposure, patching, backups, change control), putting the organisational controls in place (policies, risk assessment, vendor management, access reviews, training), and collecting evidence that they operate. In Vanta it shows up as turning failing tests green and completing the assigned tasks."),
  ("Do we need Vanta to work with you?", "No, but it helps. Vanta automates most of the evidence collection and gives both of us one view of what is outstanding. We work the same way in Drata, Secureframe and similar platforms, and we can run a SOC 2 programme without a platform if you already have one under way."),
  ("How long does SOC 2 remediation take?", "For a typical cloud-native company with a single production environment, remediation to a Type I-ready state takes weeks rather than months once someone owns it full time. A Type II report then needs an observation window, commonly three to twelve months, during which the controls have to keep operating. The triage step gives you a realistic date for your situation."),
  ("Type I or Type II?", "Type I reports on the design of your controls at a point in time; Type II reports on whether they operated effectively over a period. Most enterprise customers ultimately want Type II. A common path is to remediate, obtain a Type I to unblock deals, and start the Type II observation window immediately afterwards."),
  ("Can you work with our auditor?", "Yes. We set up auditor access in Vanta, organise the evidence the way audit firms expect, and join the calls where technical questions come up. We do not perform the audit itself; that has to be an independent CPA firm."),
  ("What happens after the report?", "SOC 2 is annual, and controls drift the moment nobody is watching. Under our managed service the Vanta tests are monitored, recurring tasks such as access reviews and restore tests happen on schedule, and drift is fixed as it appears, so the next observation window is uneventful."),
 ],
 rel=["cloud-security", "cloudops-managed-services", "cloud-backup"],
 cta={"eyebrow": "Get started", "h2": "Staring at a red Vanta dashboard?", "p": "Book a free 30-minute call. Share your screen, and we'll tell you which failing tests matter, which are quick, and how long a realistic remediation would take.", "btn": "Book a free SOC 2 triage call"},
 service_type="SOC 2 compliance and remediation",
 extra_sections=f'''<section class="section section--alt">
  <div class="container split" style="align-items:start">
    <div class="reveal">
      <span class="eyebrow">Why Vanta</span>
      <h2>How we use Vanta</h2>
      <p>Vanta is a compliance automation platform. It connects to your cloud accounts, identity provider, code host, HR and device-management tools, runs automated tests against the SOC 2 criteria continuously, and gives your auditor a single place to review evidence. It replaces the spreadsheet and the screenshot folder.</p>
      <p>What it cannot do is change your infrastructure or run your processes. That is where we come in. We treat the Vanta dashboard as the shared backlog: every failing test gets an owner, a fix and a date, and the tests stay green because the fixes are made in code and the tasks are operated, not just ticked.</p>
      <!-- TODO (Martin): if Orbit3 holds Vanta partner status (MSP or service partner), state it here and add the partner directory URL to sameAs in the Organization schema. -->
      <p>Read our guide: <a href="/insights/soc-2-remediation-guide/" style="color:var(--accent)">SOC 2 remediation: how to close the gaps Vanta finds</a>.</p>
    </div>
    <ul class="checklist checklist--grid reveal">
      <li>{I["check"]}<span><strong>Integrations done right</strong>Every in-scope account connected, resources tagged, tests assigned.</span></li>
      <li>{I["check"]}<span><strong>Tests fixed at the source</strong>Cloud controls changed in Terraform so the fix cannot drift.</span></li>
      <li>{I["check"]}<span><strong>Policies that match reality</strong>Templates adapted to how you actually work, then approved and accepted.</span></li>
      <li>{I["check"]}<span><strong>Recurring tasks operated</strong>Access reviews, restore tests, vendor reviews and training on schedule.</span></li>
      <li>{I["check"]}<span><strong>Auditor-ready evidence</strong>Automated evidence plus the manual artefacts organised in one place.</span></li>
      <li>{I["check"]}<span><strong>Continuous monitoring</strong>Failing tests caught and fixed as part of managed operations.</span></li>
    </ul>
  </div>
</section>''',
)

# =====================================================================================
#  SERVICES OVERVIEW
# =====================================================================================
def services_index():
    path = "/Services/"
    crumb_ld, crumb_html = crumbs([("Home", "/"), ("Services", None)])
    coll = {"@type": "CollectionPage", "@id": SITE + path, "url": SITE + path, "name": "Cloud & AI Consulting Services",
            "isPartOf": {"@id": f"{SITE}/#website"},
            "hasPart": [{"@type": "Service", "name": n, "url": SITE + SURL[s]} for s, n in SERVICES]}
    website = {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "Orbit3", "publisher": {"@id": f"{SITE}/#organization"}}
    spec = ""
    for s in ["cloud-adoption", "cloud-security", "soc2-compliance", "cloud-optimisation", "cloud-devops", "cloud-backup"]:
        icon = {"cloud-adoption": "map", "cloud-security": "lock", "soc2-compliance": "shield", "cloud-optimisation": "coins", "cloud-devops": "rocket", "cloud-backup": "server"}[s]
        spec += f'<div class="card card--feature reveal"><span class="card-icon">{I[icon]}</span><h3><a href="{SURL[s]}">{SNAME[s]}</a></h3><p>{BLURB[s]}</p><a class="link-arrow" href="{SURL[s]}">Learn more {I["arrow"]}</a></div>'
    if False: spec += f'<div class="card card--feature reveal"><span class="card-icon">{I["people"]}</span><h3>Not sure where to start?</h3><p>Tell us what&#39;s slowing you down and we&#39;ll point you to the right starting place, honestly, even if that&#39;s not us.</p><a class="link-arrow" href="{CAL}" target="_blank" rel="noopener noreferrer">Book a call {I["arrow"]}</a></div>'
    body = f'''<section class="page-hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    {crumb_html}
    <h1 class="measure">One partner for running your tech <span class="text-gradient">and building your AI</span></h1>
    <p class="lede measure">Managed cloud services, AI consulting and the specialist cloud work around them. We keep your cloud and IT operations secure, reliable and cost-efficient, and build the AI and automation that move your business forward.</p>
    {cta_buttons()}
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="center measure" style="margin-bottom:44px"><span class="eyebrow eyebrow--center">Where most clients start</span><h2>Cloud operations, security, DevOps and AI, from one team</h2><p>Two core services carry most of the relationship. Everything else is either a first project or an add-on once the day-to-day is under control.</p></div>
    <div class="grid grid-2">
      <div class="card card--primary reveal"><span class="card-tag">Core</span><span class="card-icon">{I["cloud"]}</span><h3><a href="{SURL["cloudops-managed-services"]}">CloudOps Managed Services</a></h3><p>Your AWS, Azure or Google Cloud environment proactively monitored, secured, patched and cost-managed by us, 24/7. One accountable partner, a named engineer, and a monthly review in plain English.</p>{checklist([("Proactive 24/7 monitoring and response", ""), ("Security, patching and access management", ""), ("FinOps cost control and backup operations", "")])}<a class="link-arrow mt-1" href="{SURL["cloudops-managed-services"]}">Explore managed services {I["arrow"]}</a></div>
      <div class="card card--primary reveal"><span class="card-tag">Core</span><span class="card-icon">{I["robot"]}</span><h3><a href="{SURL["ai-solutions"]}">AI Consulting &amp; Implementation</a></h3><p>Custom LLM applications, retrieval-augmented generation, workflow automation and AI agents, scoped for payback, built on secure cloud foundations and run as a managed service after launch.</p>{checklist([("Use-case scoping with an honest recommendation", ""), ("RAG, copilots and agents on your own data", ""), ("Evaluation, guardrails and monitoring built in", "")])}<a class="link-arrow mt-1" href="{SURL["ai-solutions"]}">Explore AI solutions {I["arrow"]}</a></div>
    </div>
  </div>
</section>
<section class="section section--alt">
  <div class="container">
    <div class="center measure" style="margin-bottom:44px"><span class="eyebrow eyebrow--center">Specialist cloud services</span><h2>Targeted help where you need it</h2><p>Engage any of these on their own, or as part of a managed-services relationship.</p></div>
    <div class="grid grid-3">{spec}</div>
  </div>
</section>
<section class="section">
  <div class="container split">
    <div class="reveal">
      <span class="eyebrow">How we work</span>
      <h2>Small enough to know your environment, experienced enough to run it</h2>
      <p>Orbit3 is a founder-led consultancy. The people who scope your work are the people who deliver it, and the engineer who onboards your environment is the one who answers when something breaks. Read more <a href="/about/">about how we work</a>.</p>
      <p>We are not tied to a vendor. We recommend the platform and the tools that fit your workloads and your team, and we write the reasoning down so you can challenge it.</p>
    </div>
    {steps([("Listen", "A free 30-minute call about what is actually slowing you down. You get a straight answer on whether we can help, and what we would do first."), ("Scope", "A written proposal with the scope, the deliverables, the timeline and the fee. No surprises, and nothing implicit."), ("Deliver and stay", "We do the work, hand over cleanly, and, for most clients, keep running the environment afterwards.")])}
  </div>
</section>
{cta_band("Get started", "Tell us what you're trying to fix", "One free call is the fastest way to know whether we can help. We'll listen, give you a straight answer, and outline what a first step would look like.")}
'''
    write(path, head(path, "Cloud & AI Consulting Services | Orbit3",
                     "Managed cloud services, AI consulting, cloud migration, security, cost optimisation, DevOps and backup from Orbit3. One accountable partner for tech and AI.",
                     [ORG, website, coll, crumb_ld]) + header(path) + body + footer())
services_index()

# =====================================================================================
#  HOME
# =====================================================================================
def home():
    path = "/"
    website = {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "Orbit3", "publisher": {"@id": f"{SITE}/#organization"}}
    grid = ""
    icons = {"cloudops-managed-services": "cloud", "ai-solutions": "robot", "cloud-adoption": "map", "cloud-security": "lock", "soc2-compliance": "shield", "cloud-optimisation": "coins", "cloud-devops": "rocket", "cloud-backup": "server"}
    for s, n in SERVICES:
        grid += f'<a class="card card--link reveal" href="{SURL[s]}"><span class="card-icon">{I[icons[s]]}</span><h3>{n}</h3><p>{BLURB[s]}</p><span class="link-arrow">Learn more {I["arrow"]}</span></a>'
    if False: grid += f'<a class="card card--link card--primary reveal" href="{CAL}" target="_blank" rel="noopener noreferrer"><span class="card-icon">{I["people"]}</span><h3>Not sure where to start?</h3><p>Tell us what is slowing you down and we will point you to the right first step, honestly, even if that is not us.</p><span class="link-arrow">Book a free call {I["arrow"]}</span></a>'
    body = f'''<section class="hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    <span class="eyebrow eyebrow--center">Managed Cloud Services &amp; AI Consulting</span>
    <h1>Your technology, <span class="text-gradient">fully managed.</span><br>Your AI, finally shipped.</h1>
    <p class="lede measure">Orbit3 is your outsourced tech team. We provide managed cloud services that keep your cloud and IT operations secure, reliable and cost-efficient, and we build the custom AI and automation that give you an edge. One accountable partner.</p>
    <div class="hero-actions">
      <a class="btn btn-primary btn-lg" href="{CAL}" target="_blank" rel="noopener noreferrer">{I["cal"]} Book a free intro call</a>
      <a class="btn btn-ghost btn-lg" href="/Services/">See what we do {I["arrow"]}</a>
    </div>
    <div class="hero-trust">Free 30-minute call · No obligation · We reply within one business day</div>
  </div>
</section>
<section class="section--tight">
  <div class="container center">
    <p class="eyebrow eyebrow--center" style="color:var(--fg-faint)">Built on the platforms you already trust</p>
    <div class="logos"><img src="/images/aws.webp" width="120" height="34" loading="lazy" alt="Amazon Web Services logo"><img src="/images/azure.webp" width="120" height="34" loading="lazy" alt="Microsoft Azure logo"><img src="/images/google-cloud-platform.webp" width="120" height="34" loading="lazy" alt="Google Cloud logo"><img src="/images/cloudflare.webp" width="120" height="34" loading="lazy" alt="Cloudflare logo"><img src="/images/terraform.webp" width="120" height="34" loading="lazy" alt="Terraform logo"><img src="/images/github.webp" width="120" height="34" loading="lazy" alt="GitHub logo"><img src="/images/red-hat.webp" width="120" height="34" loading="lazy" alt="Red Hat logo"><img src="/images/elastic.webp" width="120" height="34" loading="lazy" alt="Elastic logo"></div>
  </div>
</section>
<section class="section section--alt">
  <div class="container">
    <div class="center measure" style="margin-bottom:48px">
      <span class="eyebrow eyebrow--center">Why teams choose Orbit3</span>
      <h2>Less firefighting. More moving forward.</h2>
    </div>
    {cards3([
      {"icon": "shield", "h": "Stay secure &amp; running", "p": "24/7 monitoring, patching and proactive management of your cloud and IT. We catch and fix issues before they reach your customers."},
      {"icon": "coins", "h": "Control your spend", "p": "We right-size and govern your cloud costs with FinOps discipline, removing waste and giving you transparency over every pound."},
      {"icon": "robot", "h": "Move faster with AI", "p": "Custom AI assistants, LLM applications and workflow automation that take real work off your team's plate, then run as a managed service."},
    ])}
  </div>
</section>
<section class="section">
  <div class="container split">
    <div class="reveal">
      <span class="eyebrow">Our core service</span>
      <h2>CloudOps Managed Services</h2>
      <p>We act as an extension of your team, bringing certified expertise to proactively manage, monitor and maintain your cloud environment on AWS, Azure or Google Cloud. Secure, scalable and cost-effective, with one team accountable for it all.</p>
      {checklist([("Proactive 24/7 monitoring", "High availability, handled end to end."), ("Security &amp; compliance built in", "Controls, access and patching as standard, with <a href='/Services/cloud-security/'>cloud security reviews</a> when you need evidence."), ("Cost optimisation (FinOps)", "Visibility and control over cloud spend through continuous <a href='/Services/cloud-optimisation/'>cloud optimisation</a>.")])}
      <div class="hero-actions"><a class="link-arrow" href="{SURL["cloudops-managed-services"]}">Explore Managed Services {I["arrow"]}</a></div>
    </div>
    <div class="order-first reveal"><div class="glass-panel" aria-hidden="true">
  <div style="padding:18px 18px 6px;display:flex;align-items:center;justify-content:space-between">
    <div style="font-family:var(--font-head);font-weight:600;color:#fff">Cloud health</div>
    <span class="pill"><span class="dot"></span> All systems operational</span>
  </div>
  <div style="padding:8px 18px 18px;display:grid;gap:10px">
    <div class="glance-row"><span>Production cluster</span><span class="pill"><span class="dot"></span>Healthy</span></div>
    <div class="glance-row"><span>Security &amp; patching</span><span class="pill"><span class="dot"></span>Up to date</span></div>
    <div class="glance-row"><span>Cloud spend vs. budget</span><strong style="color:var(--accent)">On track</strong></div>
    <div class="glance-row"><span>Backups verified</span><span class="pill"><span class="dot"></span>Today</span></div>
  </div>
</div></div>
  </div>
</section>
<section class="section section--alt">
  <div class="container split">
    <div class="reveal"><div class="glass-panel" aria-hidden="true">
  <div style="padding:16px 18px;border-bottom:1px solid var(--border);font-family:var(--font-head);font-weight:600;color:#fff;display:flex;gap:8px;align-items:center"><span style="display:inline-flex;width:20px;color:var(--accent)">{I["robot"]}</span>Orbit3 AI Agent</div>
  <div style="padding:18px;display:grid;gap:12px">
    <div style="justify-self:end;max-width:78%;padding:11px 14px;background:var(--surface-2);border:1px solid var(--border);border-radius:14px 14px 4px 14px;color:var(--fg)">Summarise last week's support tickets and flag at-risk accounts.</div>
    <div style="justify-self:start;max-width:85%;padding:11px 14px;background:linear-gradient(180deg,rgba(45,212,191,.12),var(--surface));border:1px solid rgba(45,212,191,.28);border-radius:14px 14px 14px 4px;color:var(--fg)">Tickets processed and grouped by theme. Accounts showing churn signals have been flagged and routed to your CRM. Draft responses are queued for your review. <span style="color:var(--accent)">View &rarr;</span></div>
    <div style="display:flex;gap:8px;align-items:center;color:var(--fg-faint);font-size:.85rem"><span class="dot" style="width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent)"></span> Connected to Helpdesk · CRM · Cloud</div>
  </div>
</div></div>
    <div class="reveal">
      <span class="eyebrow">Growing capability</span>
      <h2>AI Consulting &amp; Implementation</h2>
      <p>From custom LLM applications to workflow automation and AI agents, we take AI from idea to production, built on secure cloud foundations and managed for the long run, so the value compounds instead of fading after launch.</p>
      {checklist([("Custom AI &amp; LLM applications", "RAG, copilots and assistants on your data."), ("Workflow automation &amp; agents", "Reliable automations that take real action.")])}
      <div class="hero-actions"><a class="link-arrow" href="{SURL["ai-solutions"]}">Explore AI Solutions {I["arrow"]}</a></div>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="center measure" style="margin-bottom:44px"><span class="eyebrow eyebrow--center">Everything we do</span><h2>Eight services, one accountable team</h2><p>Start with the one that solves today's problem. Most clients add more once the day-to-day is under control.</p></div>
    <div class="grid grid-4 grid--services">{grid}</div>
  </div>
</section>
<section class="section--tight section--alt">
  <div class="container">
    <div class="stats">
      <div class="stat reveal"><div class="stat-num">24<span>/7</span></div><div class="stat-label">Proactive monitoring</div></div>
      <div class="stat reveal"><div class="stat-num">3</div><div class="stat-label">Major clouds: AWS, Azure, GCP</div></div>
      <div class="stat reveal"><div class="stat-num">1<span>d</span></div><div class="stat-label">Reply within a business day</div></div>
      <div class="stat reveal"><div class="stat-num">100<span>%</span></div><div class="stat-label">Single-partner accountability</div></div>
    </div>
  </div>
</section>
{cta_band("Let's find your fastest win", "Book a free 30-minute intro call", "We'll look at where your tech operations are costing you time or money, and where AI could give you an edge, and tell you honestly what's worth doing first.", "Book your free intro call")}
'''
    write(path, head(path, "Managed Cloud Services & AI Consulting | Orbit3",
                     "Orbit3 provides managed cloud services and AI consulting. We run your cloud operations on AWS, Azure and Google Cloud and build custom AI. Book a free call.",
                     [ORG, website]) + header(path) + body + footer())
home()

# =====================================================================================
#  ABOUT
# =====================================================================================
def about():
    path = "/about/"
    crumb_ld, crumb_html = crumbs([("Home", "/"), ("About", None)])
    about_ld = {"@type": "AboutPage", "@id": SITE + path, "url": SITE + path, "name": "About Orbit3", "mainEntity": {"@id": f"{SITE}/#organization"}}
    body = f'''<section class="page-hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    {crumb_html}
    <h1 class="measure">A founder-led cloud and AI consultancy <span class="text-gradient">that stays accountable</span></h1>
    <p class="lede measure">Orbit3 runs cloud and IT operations for growing businesses and builds the AI and automation on top of them. This page is about who we are and how we work.</p>
  </div>
</section>
<section class="section">
  <div class="container split" style="align-items:start">
    <div class="reveal">
      <span class="eyebrow">Who we are</span>
      <h2>Who we are and how we work</h2>
      <p>Orbit3 started as a cloud consultancy: assessing technology stacks, designing target architectures and helping teams adopt AWS, Azure and Google Cloud. Clients kept asking the same question at the end of every project: "Can you just run it for us?" So we did, and <a href="/Services/cloudops-managed-services/">CloudOps managed services</a> became the core of the business.</p>
      <p>The second shift came with large language models. The businesses we ran infrastructure for wanted AI in their products and operations, and they wanted it built by people who already understood their data, their security posture and their cloud accounts. <a href="/Services/ai-solutions/">AI consulting and implementation</a> grew out of that, delivered with the same managed-service discipline: scoped for payback, built to production standards, and looked after once it is live.</p>
      <p>We are deliberately small. The people who scope your work are the people who deliver it, and the engineer who onboards your environment is the one who answers when something breaks.</p>
    </div>
    <div class="reveal">
      <div class="card card--primary">
        <span class="card-icon">{I["people"]}</span>
        <h3>Led by Martin, founder</h3>
        <p>Orbit3 is led by its founder, Martin, who works directly with every client: on the first call, in the scoping, and in the monthly reviews. That is a deliberate choice about how a consultancy should feel from the client's side.</p>
        <!-- TODO (Martin): add surname, a short bio with years of experience, named certifications and a photo (images/martin.webp, with alt text). Also add your personal LinkedIn URL to the founder entity in the Organization schema in build.py / each page's JSON-LD. -->
        <a class="link-arrow" href="{CAL}" target="_blank" rel="noopener noreferrer">Book a call with Martin {I["arrow"]}</a>
      </div>
    </div>
  </div>
</section>
<section class="section section--alt">
  <div class="container">
    <div class="center measure" style="margin-bottom:44px"><span class="eyebrow eyebrow--center">Principles</span><h2>What you can expect from us</h2></div>
    {cards3([
      {"icon": "eye", "h": "Straight answers", "p": "If AI is not the right tool, or managed services are not the right fit yet, we say so on the first call. A recommendation to wait is still a recommendation."},
      {"icon": "shield", "h": "Nothing implicit", "p": "Scope, response targets, deliverables and fees are written down before we start. You should never have to guess what we own."},
      {"icon": "refresh", "h": "Built to be operated", "p": "We design environments and AI systems we would be happy to run ourselves, because usually we do. Documentation and infrastructure as code are not optional extras."},
      {"icon": "map", "h": "Vendor-neutral", "p": "We work across AWS, Azure and Google Cloud and recommend the platform that fits your workloads and your team, with the reasoning written down."},
      {"icon": "lock", "h": "Your accounts, your data", "p": "Everything stays in your name and under your control. We work through least-privilege access you can revoke, and every change is version-controlled."},
      {"icon": "chart", "h": "Measured in outcomes", "p": "Availability, incidents, security findings, spend and delivery speed, reported monthly in plain English."},
    ])}
  </div>
</section>
<section class="section">
  <div class="container split" style="align-items:start">
    <div class="reveal">
      <span class="eyebrow">Platforms and tooling</span>
      <h2>The platforms we run every day</h2>
      <p>Our engineers hold current vendor certifications across the three major clouds and work daily with the tooling around them: Terraform for infrastructure as code, GitHub and GitLab for delivery, Kubernetes and the managed container services, Cloudflare at the edge, and Elastic and the native monitoring stacks for observability.</p>
      <!-- TODO (Martin): list the specific certifications held (e.g. AWS Certified Solutions Architect – Professional, Microsoft Certified: Azure Administrator Associate) and any partner programme memberships. Named certifications are a strong trust signal for both buyers and search engines. -->
      <p>We are not resellers. When we recommend a tool, it is because it fits your environment, not because of a margin.</p>
    </div>
    <div class="reveal"><div class="logos logos--grid"><img src="/images/aws.webp" width="120" height="34" loading="lazy" alt="Amazon Web Services logo"><img src="/images/azure.webp" width="120" height="34" loading="lazy" alt="Microsoft Azure logo"><img src="/images/google-cloud-platform.webp" width="120" height="34" loading="lazy" alt="Google Cloud logo"><img src="/images/cloudflare.webp" width="120" height="34" loading="lazy" alt="Cloudflare logo"><img src="/images/terraform.webp" width="120" height="34" loading="lazy" alt="Terraform logo"><img src="/images/github.webp" width="120" height="34" loading="lazy" alt="GitHub logo"><img src="/images/red-hat.webp" width="120" height="34" loading="lazy" alt="Red Hat logo"><img src="/images/elastic.webp" width="120" height="34" loading="lazy" alt="Elastic logo"></div></div>
  </div>
</section>
<section class="section section--alt">
  <div class="container split" style="align-items:start">
    <div class="reveal">
      <span class="eyebrow">Working with us</span>
      <h2>How an engagement starts</h2>
      <p>Every relationship begins the same way, whether it becomes a one-off project or a multi-year managed service.</p>
    </div>
    {steps([("A free 30-minute call", "You describe what is slowing you down. We ask questions, tell you what we would look at first, and give you a straight answer on whether we can help."), ("A written proposal", "Scope, deliverables, timeline and fee in plain English. For managed services, that includes what we monitor, what we fix without asking and what we escalate."), ("Discovery, then delivery", "We start with an assessment you own whether or not you continue, then do the work, hand over cleanly, and for most clients keep running the environment afterwards.")])}
  </div>
</section>
{cta_band("Get in touch", "Talk to the people who will do the work", "Book a free intro call or send a message. We reply within one business day.")}
'''
    write(path, head(path, "About Orbit3 | Founder-led Cloud & AI Consultancy",
                     "Orbit3 is a founder-led managed cloud services and AI consultancy. Who we are, how we work, the platforms we run and what to expect from an engagement.",
                     [ORG, about_ld, crumb_ld]) + header(path) + body + footer())
about()

# =====================================================================================
#  CONTACT
# =====================================================================================
def contact():
    path = "/contact/"
    crumb_ld, crumb_html = crumbs([("Home", "/"), ("Contact", None)])
    cp = {"@type": "ContactPage", "@id": SITE + path, "url": SITE + path, "name": "Contact Orbit3", "mainEntity": {"@id": f"{SITE}/#organization"}}
    body = f'''<section class="page-hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    {crumb_html}
    <h1 class="measure">Let's talk</h1>
    <p class="lede measure">The fastest way to get started is a free 30-minute intro call. Prefer to write? Use the form. We reply within one business day.</p>
  </div>
</section>
<section class="section" style="padding-top:8px">
  <div class="container split" style="align-items:start">
    <div class="card reveal">
      <h2 style="font-size:1.5rem">Send us a message</h2>
      <p>Tell us about your project and we'll figure out the best option. Prefer email? <a href="mailto:hello@orbit3.io" style="color:var(--accent)">hello@orbit3.io</a></p>
      <form class="form mt-1" action="https://formspree.io/martin@orbit3.io" method="POST" name="email-form">
        <div class="field"><label for="name">Name</label><input class="input" type="text" id="name" name="name" placeholder="Your name" autocomplete="name" required></div>
        <div class="field"><label for="email">Email</label><input class="input" type="email" id="email" name="email" placeholder="you@company.com" autocomplete="email" required></div>
        <div class="field"><label for="Phone">Phone <span style="color:var(--fg-faint)">(optional)</span></label><input class="input" type="tel" id="Phone" name="Phone" placeholder="+44 ..." autocomplete="tel"></div>
        <div class="field"><label for="Message">How can we help?</label><textarea class="textarea" id="Message" name="Message" placeholder="A sentence or two about what you're trying to achieve." required></textarea></div>
        <button class="btn btn-primary btn-block btn-lg" type="submit">Send message</button>
      </form>
    </div>
    <div class="reveal">
      <div class="card card--primary">
        <span class="card-icon">{I["cal"]}</span>
        <h3>Rather just talk?</h3>
        <p>Grab a time that suits you and we'll have a no-pressure conversation about what you're trying to achieve.</p>
        <a class="btn btn-primary btn-block mt-1" href="{CAL}" target="_blank" rel="noopener noreferrer">{I["cal"]} Book a free intro call</a>
      </div>
      <div class="card mt-2">
        <h3 style="font-size:1.12rem;margin-bottom:14px">Connect</h3>
        <ul class="checklist">
          <li>{I["mail"]}<span><a href="mailto:hello@orbit3.io" style="color:var(--fg)">hello@orbit3.io</a></span></li>
          <li>{I["linkedin"]}<span><a href="{LINKEDIN}" target="_blank" rel="noopener noreferrer" style="color:var(--fg)">linkedin.com/company/orbit3</a></span></li>
        </ul>
      </div>
      <div class="card mt-2">
        <h3 style="font-size:1.12rem;margin-bottom:10px">What to expect</h3>
        <p>A reply within one business day. On the call we'll ask about your environment or your AI idea, tell you what we would look at first, and give you a straight answer on whether we're the right fit. No pitch deck.</p>
      </div>
    </div>
  </div>
</section>
'''
    write(path, head(path, "Contact Orbit3 | Book a Free Cloud & AI Intro Call",
                     "Book a free 30-minute intro call with Orbit3 or send a message. Managed cloud services and AI consulting. We reply within one business day.",
                     [ORG, cp, crumb_ld]) + header(path) + body + footer())
contact()

# =====================================================================================
#  INSIGHTS (blog)
# =====================================================================================
AUTHOR = {"@type": "Person", "@id": f"{SITE}/about/#founder", "name": "Martin", "jobTitle": "Founder, Orbit3", "url": f"{SITE}/about/"}

SOC2_GUIDE_BODY = '''
<p>You connected AWS, Google Workspace and GitHub to Vanta on Monday. By Tuesday the dashboard showed 60-odd failing tests, a policy library nobody has read, and a list of tasks assigned to people who did not know they were on the hook. Welcome to SOC 2 remediation: the part of the project that sits between "we bought the tool" and "we have the report", and the part where most SOC 2 timelines quietly slip.</p>
<p>This guide is for founders, CTOs and the engineer who drew the short straw. It explains what remediation actually involves, why the first Vanta scan looks so bad, which gaps to fix first, how to sequence the work into a realistic plan, and the mistakes that turn a six-week project into a six-month one.</p>

<h2 id="what-is-remediation">What SOC 2 remediation actually means</h2>
<p>SOC 2 is an attestation report, written by an independent CPA firm, on the controls your company operates against the AICPA's <strong>Trust Services Criteria</strong>. The Security criteria (also called the Common Criteria) are mandatory. Availability, Confidentiality, Processing Integrity and Privacy are optional and you include them only if your customers need them.</p>
<p>A SOC 2 project has four phases, and remediation is the third:</p>
<ol>
  <li><strong>Scoping.</strong> Which systems, which people, which criteria, and whether you are going for a Type I or a Type II report.</li>
  <li><strong>Gap assessment.</strong> Comparing what you actually do against what the criteria require. In Vanta this is largely automated: the integrations run tests continuously and each failing test is a gap.</li>
  <li><strong>Remediation.</strong> Closing the gaps. Changing cloud configuration, writing and adopting policies, setting up recurring processes, and producing evidence that all of it happens.</li>
  <li><strong>Audit.</strong> A Type I examines control design at a point in time. A Type II examines whether the controls operated effectively over an observation window, commonly three to twelve months.</li>
</ol>
<p>Remediation is where the engineering lives. Vanta will tell you that an S3 bucket is public or that three staff have not completed security training. It will not make the bucket private or sit the training for them. Someone has to own each item, and that ownership gap is the single biggest reason SOC 2 projects stall.</p>

<h2 id="why-vanta-is-red">Why Vanta shows so many failing tests on day one</h2>
<p>Compliance automation platforms work by connecting to the systems where your controls live and checking them against the criteria on a schedule. Vanta's integrations cover cloud providers (AWS, Azure, Google Cloud), identity providers (Google Workspace, Microsoft Entra, Okta), code hosts (GitHub, GitLab), HR systems, device management and a long tail of SaaS tools. Each integration enables a set of automated tests.</p>
<p>The first scan is red for three reasons:</p>
<ul>
  <li><strong>It tests everything in the connected account</strong>, including the sandbox project from two years ago and the database nobody remembers. Before you fix anything, mark what is out of scope so the dashboard reflects the environment you are actually attesting to.</li>
  <li><strong>Cloud defaults are not SOC 2 defaults.</strong> A fresh cloud account does not have audit logging retained for a year, encryption enforced everywhere, MFA required for every human, or alerts routed to a person. All of that is configuration you have to add.</li>
  <li><strong>Half the tests are about people, not systems.</strong> Policy acceptance, security training, background checks, offboarding, access reviews and vendor reviews all fail until the underlying process exists and has been run at least once.</li>
</ul>
<p>A typical first scan for a cloud-native company of 20 to 100 people looks something like this:</p>
<div class="table-wrap"><table>
  <thead><tr><th>Area</th><th>What typically fails</th><th>Who fixes it</th></tr></thead>
  <tbody>
    <tr><td>Identity and access</td><td>MFA not enforced for all users, root or owner accounts in daily use, no quarterly access review, shared credentials</td><td>Engineering</td></tr>
    <tr><td>Logging and monitoring</td><td>Audit logs not enabled in every region, retention shorter than a year, no alerting on suspicious activity</td><td>Engineering</td></tr>
    <tr><td>Encryption</td><td>Unencrypted volumes, snapshots or databases; buckets without default encryption; TLS not enforced</td><td>Engineering</td></tr>
    <tr><td>Network exposure</td><td>Public storage buckets, security groups open to the internet, databases with public endpoints</td><td>Engineering</td></tr>
    <tr><td>Vulnerability management</td><td>No scanning, findings older than the SLA, unpatched instances or containers</td><td>Engineering</td></tr>
    <tr><td>Change management</td><td>No branch protection, changes merged without review, production deployed from laptops</td><td>Engineering</td></tr>
    <tr><td>Backup and recovery</td><td>Backups not enabled for every data store, no restore test on record, no documented recovery plan</td><td>Engineering</td></tr>
    <tr><td>Policies</td><td>Policies not written, not approved, or not accepted by staff</td><td>Leadership</td></tr>
    <tr><td>People</td><td>Security training incomplete, background checks missing, offboarding not evidenced</td><td>Operations / HR</td></tr>
    <tr><td>Vendors and risk</td><td>No vendor inventory or reviews, no risk assessment on record</td><td>Leadership</td></tr>
  </tbody>
</table></div>

<h2 id="fix-first">The eight gaps to fix first</h2>
<p>Not every failing test carries the same weight. Auditors focus on the controls that protect customer data and on whether you can show they operate consistently. This is the order we work in, because it removes the most audit risk per hour of effort.</p>

<h3>1. Identity and multi-factor authentication</h3>
<p>Enforce MFA for every human account in your identity provider and your cloud consoles, retire shared logins, stop using root or global-admin accounts for day-to-day work, and put a break-glass procedure around them. In AWS that means IAM Identity Center or SSO with MFA enforced by policy; in Azure, Conditional Access; in Google Cloud, enforced 2-step verification at the organisation level. This is the control auditors ask about first and it usually clears a cluster of tests at once.</p>

<h3>2. Audit logging and retention</h3>
<p>Turn on audit logging in every region and every account (CloudTrail organisation trails, Azure Activity Log to Log Analytics, Cloud Audit Logs with a retained sink), set retention to at least a year, protect the logs from deletion, and route at least a handful of high-signal alerts to a channel someone reads. You need the logs to exist before the observation window starts, because the auditor will sample from it.</p>

<h3>3. Encryption at rest and in transit</h3>
<p>Enable default encryption for block storage, object storage, databases and snapshots. Enforce TLS on load balancers and storage endpoints. Most of this is a one-line setting per service, and once it is in infrastructure code it stays fixed.</p>

<h3>4. Network exposure</h3>
<p>Close public buckets, remove 0.0.0.0/0 rules that are not on a load balancer, move databases to private subnets and put a bastion or a zero-trust proxy in front of anything that must be reachable. Vanta's tests here are blunt, which is helpful: they will not go green until the exposure is actually gone.</p>

<h3>5. Vulnerability management and patching</h3>
<p>Turn on the native scanner (Amazon Inspector, Defender for Cloud, Security Command Center), add dependency and container scanning to CI, and define a remediation SLA by severity that you can actually meet. Then meet it. The test is not "do you scan" but "do you fix findings within the time your own policy states".</p>

<h3>6. Backup and restore testing</h3>
<p>Every in-scope data store needs an automated backup with a retention policy, and you need at least one documented restore test on record before the audit. If you have never restored from a backup, do it during remediation and keep the timing and the screenshot. Our <a href="/Services/cloud-backup/">cloud backup service</a> covers this in more depth.</p>

<h3>7. Change management</h3>
<p>Branch protection on the production branch, mandatory peer review, CI checks that must pass, and a deploy path that goes through the pipeline rather than a laptop. Vanta evidences this straight from GitHub or GitLab, so once the settings are on, the tests stay green without anyone doing anything.</p>

<h3>8. Access reviews and offboarding</h3>
<p>Set up a quarterly access review as a recurring task in Vanta, run the first one now, and write the offboarding checklist so that the next leaver's access is removed within your policy's timeframe and the evidence is captured. Auditors sample joiners and leavers during the observation window, and this is where Type II exceptions most often come from.</p>

<h2 id="technical-vs-organisational">Technical gaps versus organisational gaps</h2>
<p>Engineering can close the first seven items above in a few focused weeks. The organisational controls take longer in calendar time, not because they are hard but because they involve people and recurring dates:</p>
<ul>
  <li><strong>Policies.</strong> Vanta ships templates for every policy SOC 2 expects. Do not accept them verbatim. Edit each one to describe what your company actually does, because the auditor will test your practice against your policy, and a policy that promises a 30-day patch SLA you do not meet is worse than one that promises 60 and does.</li>
  <li><strong>Risk assessment.</strong> A written, dated assessment of the risks to your service and what you do about them, reviewed at least annually. It should mention your real risks, not generic ones.</li>
  <li><strong>Vendor management.</strong> An inventory of the third parties that touch customer data, with a review of each (their SOC 2 report, their security page, a questionnaire) and a record of the decision.</li>
  <li><strong>Security awareness training.</strong> Every employee, on joining and annually. Vanta tracks completion.</li>
  <li><strong>Background checks.</strong> Where your policy and local law require them, evidenced through your HR system.</li>
</ul>
<div class="callout"><p><strong>Rule of thumb:</strong> a technical control is done when it is in code. An organisational control is done when it has run once, on the date it was supposed to, with evidence. A control that exists only as a document is not done.</p></div>

<h2 id="sequence">A realistic sequence: the 90-day plan</h2>
<p>Timelines vary with the size of the environment and how much attention the work gets, but for a single-product SaaS company with one production environment, this sequence works:</p>
<ol>
  <li><strong>Weeks 1 to 2: scope and triage.</strong> Decide the criteria, mark out-of-scope resources in Vanta, assign an owner to every failing test and rank the backlog by audit risk and effort. Agree the target: usually Type I first.</li>
  <li><strong>Weeks 3 to 6: technical remediation.</strong> Work the eight areas above, in that order, through infrastructure as code. Re-run the Vanta tests as you go rather than at the end.</li>
  <li><strong>Weeks 7 to 10: organisational controls.</strong> Finalise and approve policies, run the risk assessment, complete vendor reviews, get training and policy acceptance to 100 percent, and run the first access review.</li>
  <li><strong>Weeks 11 to 12: evidence and pre-audit.</strong> Collect the manual evidence Vanta cannot automate, give the auditor access, and walk through the environment with them before fieldwork.</li>
  <li><strong>Then: the observation window.</strong> If you want a Type II, the window starts once the controls are in place. During it, the recurring tasks must actually happen on schedule. Nothing in this phase is difficult, but all of it has to be done.</li>
</ol>

<h2 id="mistakes">Five mistakes that stall SOC 2 remediation</h2>
<ol>
  <li><strong>Fixing tests by hand in the console.</strong> The test goes green today and red again in a month when someone recreates the resource. Make the change in Terraform, CloudFormation, Bicep or whatever your environment is defined in. If it is not defined in code, that is your first remediation item.</li>
  <li><strong>Scoping too broadly.</strong> Attesting to every account, environment and tool you own multiplies the work. Scope to the systems that process customer data and the people who can access them.</li>
  <li><strong>Treating a green dashboard as audit-ready.</strong> Vanta's tests cover what it can see through integrations. Auditors will also ask for things it cannot see: meeting minutes, incident records, the restore test, the signed vendor review. Keep a folder for these from week one.</li>
  <li><strong>Ignoring the observation window.</strong> Teams sprint to a Type I and then relax. Every missed access review or late restore test during the Type II window becomes an exception in the report that your customers will read.</li>
  <li><strong>Having no single owner.</strong> Remediation is an engineering project with a backlog and a date, and it needs the same ownership as any other. If nobody's name is on it, it will not happen between sprints.</li>
</ol>

<h2 id="type-1-vs-type-2">Type I or Type II: what to remediate for</h2>
<p>Remediate for Type II from the start, even if the first report you obtain is a Type I. The controls are the same; the difference is that Type II proves they operate over time. Designing them from the beginning as recurring, evidenced processes costs nothing extra and avoids a second remediation effort when the observation window begins. Most enterprise procurement teams accept a Type I as a bridge and expect a Type II to follow.</p>

<h2 id="orbit3">Where Orbit3 fits</h2>
<p>We run <a href="/Services/soc2-compliance/">SOC 2 remediation as a service</a>, working inside your Vanta workspace. We triage the failing tests, fix the cloud controls in code, run the organisational controls with you, organise the evidence and support the audit. For most clients the work then rolls into <a href="/Services/cloudops-managed-services/">managed cloud operations</a>, where the Vanta tests are monitored and the recurring tasks are operated every month, so the next observation window is uneventful. If you are on Drata or Secureframe instead of Vanta, the approach is identical.</p>
<p>If you are looking at a red dashboard and a date you are not sure you can hit, <a href="/contact/">get in touch</a>. Share your screen on a free 30-minute call and we will tell you which tests matter, which are quick, and how long a realistic remediation would take.</p>
'''

POSTS = [
 {
  "slug": "soc-2-remediation-guide",
  "title": "SOC 2 Remediation: How to Close the Gaps Vanta Finds",
  "seo_title": "SOC 2 Remediation Guide: Fixing the Gaps Vanta Finds | Orbit3",
  "desc": "A practical SOC 2 remediation guide: why Vanta shows failing tests on day one, the eight gaps to fix first, a 90-day plan, and the mistakes that stall the audit.",
  "category": "Compliance",
  "date": "2026-09-02", "updated": "2026-09-02",
  "summary": "Why the first Vanta scan is red, which failing tests to fix first, how to sequence remediation into a 90-day plan, and the five mistakes that turn a six-week project into a six-month one.",
  "keywords": ["SOC 2 remediation", "SOC 2 compliance", "Vanta", "SOC 2 gap assessment", "SOC 2 Type II", "Trust Services Criteria", "compliance automation"],
  "body": SOC2_GUIDE_BODY,
  "faqs": [
   ("How long does SOC 2 remediation take with Vanta?", "For a cloud-native company with one production environment and an owner assigned full time, technical remediation typically takes a few weeks and organisational controls a few more. A Type I report can follow soon after; a Type II needs an observation window of three to twelve months during which the controls keep operating."),
   ("Does Vanta fix the failing tests for you?", "No. Vanta detects gaps and collects evidence through its integrations. Fixing a failing test means changing your cloud configuration, adopting a policy or running a process, which your team or a partner such as Orbit3 has to do."),
   ("Which SOC 2 criteria do we need?", "The Security criteria are mandatory. Availability, Confidentiality, Processing Integrity and Privacy are optional. Ask your customers what they need; most SaaS companies start with Security and add Availability or Confidentiality when a customer contract requires it."),
   ("Should we get a Type I or go straight to Type II?", "A common path is to obtain a Type I to unblock deals, then start the Type II observation window immediately. Remediate for Type II from the start, because the controls are the same and only the evidence period differs."),
   ("What evidence does Vanta not collect automatically?", "Anything that does not live in an integrated system: incident records, meeting minutes for risk reviews, restore test results, signed vendor assessments and some HR documents. Keep a folder for these from the start of remediation."),
  ],
  "related": ["soc2-compliance", "cloud-security", "cloudops-managed-services"],
 },
]

def reading_time(html_body):
    words = len(re.sub(r"<[^>]+>", " ", html_body).split())
    return words, max(1, round(words / 220))

def post_page(post):
    path = f"/insights/{post['slug']}/"
    url = SITE + path
    crumb_ld, crumb_html = crumbs([("Home", "/"), ("Insights", "/insights/"), (post["title"], None)])
    faq_ld, faq_html = faq_section(post["faqs"])
    words, mins = reading_time(post["body"])
    article = {"@type": "BlogPosting", "@id": url + "#article", "headline": post["title"], "description": post["desc"], "url": url,
               "mainEntityOfPage": {"@type": "WebPage", "@id": url}, "datePublished": post["date"], "dateModified": post["updated"],
               "author": AUTHOR, "publisher": {"@id": f"{SITE}/#organization"},
               "image": f"{SITE}/images/og-image.png", "articleSection": post["category"], "keywords": ", ".join(post["keywords"]),
               "wordCount": words, "inLanguage": "en-GB", "isPartOf": {"@id": f"{SITE}/insights/#blog"}}
    toc = "".join(f'<li><a href="#{m.group(1)}">{m.group(2)}</a></li>' for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', post["body"]))
    nice_date = __import__("datetime").date.fromisoformat(post["date"]).strftime("%-d %B %Y")
    rel_cards = "".join(f'<a class="card card--link reveal" href="{SURL[s]}"><h3>{SNAME[s]}</h3><p>{BLURB[s]}</p><span class="link-arrow">Learn more {I["arrow"]}</span></a>' for s in post["related"])
    body = f'''<section class="page-hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    {crumb_html}
    <span class="eyebrow eyebrow--center">{post["category"]}</span>
    <h1 class="measure" style="font-size:clamp(2rem,4.4vw,3.3rem)">{post["title"]}</h1>
    <p class="lede measure">{post["summary"]}</p>
    <div class="post-meta"><span>By <a href="/about/">Martin, Founder</a></span><span>Published <time datetime="{post["date"]}">{nice_date}</time></span><span>{mins} min read</span></div>
  </div>
</section>
<article class="section" style="padding-top:16px">
  <div class="container post">
    <nav class="toc" aria-label="In this article"><div class="toc-title">In this guide</div><ol>{toc}</ol></nav>
    <div class="prose">{post["body"]}</div>
    <div class="card card--primary author-card mt-2">
      <span class="card-icon">{I["people"]}</span>
      <div><h3 style="font-size:1.1rem">About the author</h3><p>Martin is the founder of Orbit3, a managed cloud services and AI consultancy. He works directly with every client on cloud operations, security and compliance. <a href="/about/" style="color:var(--accent)">More about Orbit3</a>.</p></div>
    </div>
  </div>
</article>
{faq_html}
<section class="section">
  <div class="container">
    <div class="center measure" style="margin-bottom:40px"><span class="eyebrow eyebrow--center">Related services</span><h2>How we can help</h2></div>
    <div class="grid grid-3">{rel_cards}</div>
  </div>
</section>
{cta_band("Get started", "Staring at a red Vanta dashboard?", "Book a free 30-minute call. Share your screen and we'll tell you which failing tests matter, which are quick, and how long a realistic remediation would take.", "Book a free SOC 2 triage call")}
'''
    html_out = head(path, post["seo_title"], post["desc"], [ORG, article, crumb_ld, faq_ld]) + header(path) + body + footer()
    html_out = html_out.replace('<meta property="og:type" content="website">', '<meta property="og:type" content="article">\n<meta property="article:published_time" content="' + post["date"] + '">\n<meta property="article:modified_time" content="' + post["updated"] + '">\n<meta property="article:author" content="' + SITE + '/about/">')
    write(path, html_out)

def insights_index():
    path = "/insights/"
    crumb_ld, crumb_html = crumbs([("Home", "/"), ("Insights", None)])
    blog = {"@type": "Blog", "@id": f"{SITE}/insights/#blog", "url": SITE + path, "name": "Orbit3 Insights",
            "description": "Practical guides on managed cloud operations, security, compliance, cost and AI from Orbit3.",
            "publisher": {"@id": f"{SITE}/#organization"},
            "blogPost": [{"@type": "BlogPosting", "@id": f"{SITE}/insights/{p['slug']}/#article", "headline": p["title"], "url": f"{SITE}/insights/{p['slug']}/", "datePublished": p["date"]} for p in POSTS]}
    cards = ""
    for p in sorted(POSTS, key=lambda x: x["date"], reverse=True):
        words, mins = reading_time(p["body"])
        nice_date = __import__("datetime").date.fromisoformat(p["date"]).strftime("%-d %B %Y")
        cards += f'<a class="card card--link reveal" href="/insights/{p["slug"]}/"><div class="post-kicker"><span class="cat">{p["category"]}</span><span>{nice_date}</span><span>{mins} min read</span></div><h2 style="font-size:clamp(1.3rem,2.2vw,1.7rem)">{p["title"]}</h2><p>{p["summary"]}</p><span class="link-arrow">Read the guide {I["arrow"]}</span></a>'
    body = f'''<section class="page-hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    {crumb_html}
    <h1 class="measure">Insights</h1>
    <p class="lede measure">Practical guides on running cloud operations, passing audits, controlling spend and shipping AI, written by the people who do it for clients every week.</p>
  </div>
</section>
<section class="section" style="padding-top:8px">
  <div class="container" style="max-width:860px">
    <div class="post-list">{cards}</div>
  </div>
</section>
{cta_band("Get in touch", "Have a question these guides don't answer?", "Book a free 30-minute call or send a message. We reply within one business day.")}
'''
    write(path, head(path, "Insights: Cloud, Compliance & AI Guides | Orbit3",
                     "Practical guides from Orbit3 on managed cloud operations, SOC 2 compliance, cloud security, cost optimisation and AI implementation.",
                     [ORG, blog, crumb_ld]) + header(path) + body + footer())

for _p in POSTS:
    post_page(_p)
insights_index()

# =====================================================================================
#  SITEMAP (HTML) and 404
# =====================================================================================
def sitemap_html():
    path = "/sitemap.html"
    links = [("Home", "/"), ("Services", "/Services/")] + [(n, SURL[s]) for s, n in SERVICES] + [("Insights", "/insights/")] + [(pp["title"], f"/insights/{pp['slug']}/") for pp in POSTS] + [("About Orbit3", "/about/"), ("Contact", "/contact/")]
    lis = "".join(f'<li>{I["check"]}<span><a href="{u}" style="color:var(--fg)">{n}</a></span></li>' for n, u in links)
    body = f'''<section class="page-hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    <h1 class="measure">Sitemap</h1>
    <p class="lede measure">Every page on the Orbit3 site.</p>
  </div>
</section>
<section class="section" style="padding-top:8px">
  <div class="container" style="max-width:680px">
    <div class="card reveal"><ul class="checklist">{lis}<li>{I["check"]}<span><a href="{CAL}" target="_blank" rel="noopener noreferrer" style="color:var(--fg)">Book a call</a></span></li></ul></div>
  </div>
</section>
'''
    write(path, head(path, "Sitemap | Orbit3", "Sitemap for Orbit3, managed cloud services and AI consulting.", [ORG], robots="noindex, follow") + header(path) + body + footer())
sitemap_html()

def legacy_js(legacy):
    return ("<script>\n(function(){\n  var map=" + json.dumps(legacy) + ";\n"
            "  var p=location.pathname.toLowerCase().replace(/\\/+$/,'');\n"
            "  var t=map[p]||map[p+'/'];\n"
            "  if(t&&t!==location.pathname){location.replace(t+location.search+location.hash);}\n"
            "})();\n</script>\n")

def not_found():
    path = "/404.html"
    links = "".join(f'<a class="card card--link reveal" href="{SURL[s]}"><h3>{n}</h3><p>{BLURB[s]}</p><span class="link-arrow">Learn more {I["arrow"]}</span></a>' for s, n in SERVICES)
    links += f'<a class="card card--link card--primary reveal" href="/contact/"><h3>Looking for something else?</h3><p>Tell us what you were trying to find and we will point you to it.</p><span class="link-arrow">Contact us {I["arrow"]}</span></a>'
    # Map of legacy URLs (lower-cased) to their new homes, for visitors arriving via old links.
    legacy = {
     "/services/manage-cloud-service.html": SURL["cloudops-managed-services"],
     "/services/cloudops-managedservices.html": SURL["cloudops-managed-services"],
     "/services/ai-solutions.html": SURL["ai-solutions"],
     "/services/cloud-adoption.html": SURL["cloud-adoption"],
     "/services/cloud-security.html": SURL["cloud-security"],
     "/services/cloud-optimisaion.html": SURL["cloud-optimisation"],
     "/services/cloud-devps.html": SURL["cloud-devops"],
     "/services/cloud-backup.html": SURL["cloud-backup"],
     "/services/services.html": "/Services/",
     "/services/": "/Services/",
     "/about-us.html": "/about/",
     "/contact.html": "/contact/",
     "/blog/blog.html": "/",
     "/index.html": "/",
    }
    body = f'''<section class="page-hero center">
  <div class="aurora" aria-hidden="true"><span class="blob"></span></div>
  <div class="hero-grid-overlay" aria-hidden="true"></div>
  <div class="container">
    <span class="eyebrow eyebrow--center">404</span>
    <h1 class="measure">That page isn't here</h1>
    <p class="lede measure">The link may be out of date, or the page may have moved. Everything we do is one click below.</p>
    <div class="hero-actions">
      <a class="btn btn-primary btn-lg" href="/">{I["arrow"]} Back to the home page</a>
      <a class="btn btn-ghost btn-lg" href="/contact/">Contact us {I["arrow"]}</a>
    </div>
  </div>
</section>
<section class="section" style="padding-top:8px">
  <div class="container">
    <h2 class="center" style="margin-bottom:32px">Where to next</h2>
    <div class="grid grid-3 grid--services">{links}</div>
  </div>
</section>
''' + legacy_js(legacy)
    content = head(path, "Page not found | Orbit3", "The page you were looking for isn't here. Find Orbit3's managed cloud services, AI consulting and contact details.", [ORG], robots="noindex, follow") + header(path) + body + footer()
    content = content.replace('<link rel="canonical" href="https://orbit3.io/404.html">\n', "")
    write(path, content)
not_found()

# =====================================================================================
#  REDIRECT STUBS for every URL that moved
# =====================================================================================
stub("/Services/services.html", "/Services/", "Services")
stub("/Services/manage-cloud-service.html", SURL["cloudops-managed-services"], "CloudOps Managed Services")
stub("/Services/cloudops-managedservices.html", SURL["cloudops-managed-services"], "CloudOps Managed Services")
stub("/Services/ai-solutions.html", SURL["ai-solutions"], "AI Solutions")
stub("/Services/cloud-adoption.html", SURL["cloud-adoption"], "Cloud Adoption")
stub("/Services/cloud-security.html", SURL["cloud-security"], "Cloud Security")
stub("/Services/cloud-optimisaion.html", SURL["cloud-optimisation"], "Cloud Optimisation")
stub("/Services/cloud-devps.html", SURL["cloud-devops"], "Cloud DevOps")
stub("/Services/cloud-backup.html", SURL["cloud-backup"], "Cloud Backup")
stub("/contact.html", "/contact/", "Contact")
stub("/about-us.html", "/about/", "About")

# =====================================================================================
#  sitemap.xml and robots.txt
# =====================================================================================
urls = [("/", "1.0"), ("/Services/", "0.9"), (SURL["cloudops-managed-services"], "0.9"), (SURL["ai-solutions"], "0.9"),
        (SURL["cloud-adoption"], "0.7"), (SURL["cloud-security"], "0.7"), (SURL["soc2-compliance"], "0.8"), (SURL["cloud-optimisation"], "0.7"), (SURL["cloud-devops"], "0.7"), (SURL["cloud-backup"], "0.7"),
        ("/about/", "0.6"), ("/contact/", "0.6"), ("/insights/", "0.6")] + [(f"/insights/{pp['slug']}/", "0.7") for pp in POSTS]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u, p in urls:
    sm += f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>{p}</priority></url>\n"
sm += "</urlset>\n"
open("sitemap.xml", "w").write(sm); print("wrote sitemap.xml")
open("robots.txt", "w").write(f"User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {SITE}/sitemap.xml\n"); print("wrote robots.txt")
