#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学科视域（System）静态站生成器
================================
把仓库根目录下的 Markdown 源（README / 00-总说 / 板块/* / 边界清单 / 图/*）
渲染成一套可导航的静态网站，输出到 docs/，用于 GitHub Pages。

源 Markdown 是唯一真相；改完 .md 后重跑本脚本即可重新生成整站：

    python3 build_site.py

依赖：pip install markdown
"""
import os
import re
import shutil

from markdown import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
ASSETS = os.path.join(DOCS, "assets")
IMG_DST = os.path.join(DOCS, "图")

# 十二个板块：序号 -> 标题（标题用于侧边栏与页脚）
SECTIONS = [
    (1,  "如何描述世界"),
    (2,  "世界由什么构成"),
    (3,  "物质如何转化"),
    (4,  "生命的分子"),
    (5,  "能量如何流动"),
    (6,  "信息如何传递"),
    (7,  "细胞是什么"),
    (8,  "生物体如何运作"),
    (9,  "多样性从哪来"),
    (10, "如何把发现变成产品"),
    (11, "如何在不确定中判断"),
    (12, "人如何一起做事"),
]

SITE_TITLE = "学科视域"
SITE_SUB = "第二版 · 按世界自身的层次重排的通识底稿"

MD_EXT = [
    "tables",
    "fenced_code",
    "toc",
    "sane_lists",
    "attr_list",
    "footnotes",
    "md_in_html",
]

# --------------------------------------------------------------------------
# 样式（内嵌，生成时写入 docs/assets/style.css）
# --------------------------------------------------------------------------
CSS = """\
:root{
  --bg:#ffffff;
  --fg:#1f2328;
  --muted:#656d76;
  --border:#d8dee4;
  --soft:#f6f8fa;
  --accent:#4f46e5;
  --accent-soft:#eef2ff;
  --quote-border:#4f46e5;
  --maxw:820px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",
    "Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  color:var(--fg);
  background:var(--bg);
  line-height:1.8;
  font-size:17px;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}

/* 顶栏 */
.site-header{
  position:sticky;top:0;z-index:20;
  display:flex;align-items:center;gap:12px;
  padding:14px 22px;
  background:rgba(255,255,255,.9);
  backdrop-filter:saturate(180%) blur(8px);
  border-bottom:1px solid var(--border);
}
.site-header .brand{font-weight:700;font-size:18px;letter-spacing:.5px}
.site-header .brand small{color:var(--muted);font-weight:400;margin-left:8px;font-size:13px}
.site-header .spacer{flex:1}
.site-header .top-link{color:var(--muted);font-size:14px;margin-left:14px}

/* 布局 */
.layout{display:flex;align-items:flex-start;max-width:1180px;margin:0 auto}
.sidebar{
  position:sticky;top:59px;align-self:flex-start;
  width:264px;flex:none;height:calc(100vh - 59px);overflow-y:auto;
  padding:22px 14px 40px 22px;border-right:1px solid var(--border);
}
.sidebar .nav-group{font-size:12px;letter-spacing:1px;color:var(--muted);
  text-transform:uppercase;margin:18px 8px 6px}
.sidebar a{
  display:block;padding:7px 10px;border-radius:8px;color:var(--fg);
  font-size:15px;line-height:1.4;
}
.sidebar a .num{display:inline-block;min-width:22px;color:var(--muted);font-variant-numeric:tabular-nums}
.sidebar a:hover{background:var(--soft);text-decoration:none}
.sidebar a.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
.sidebar a.active .num{color:var(--accent)}

/* 正文 */
.content{flex:1;min-width:0;padding:34px 40px 80px}
.content-inner{max-width:var(--maxw);margin:0 auto}
.content h1{font-size:30px;line-height:1.3;margin:.2em 0 .6em}
.content h2{font-size:23px;margin:1.8em 0 .6em;padding-bottom:.25em;border-bottom:1px solid var(--border)}
.content h3{font-size:19px;margin:1.5em 0 .5em}
.content h4{font-size:16px;margin:1.2em 0 .4em;color:var(--muted)}
.content p{margin:.7em 0}
.content ul,.content ol{padding-left:1.6em}
.content li{margin:.3em 0}
.content hr{border:none;border-top:1px solid var(--border);margin:2em 0}
.content img{max-width:100%;height:auto;display:block;margin:1.4em auto;
  border:1px solid var(--border);border-radius:10px;background:#fff;padding:8px}
.content code{background:var(--soft);padding:.15em .4em;border-radius:5px;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.88em}
.content pre{background:#0d1117;color:#e6edf3;padding:16px;border-radius:10px;
  overflow:auto;font-size:14px;line-height:1.6}
.content pre code{background:none;padding:0;color:inherit}
.content blockquote{
  margin:1.2em 0;padding:.7em 1.1em;
  border-left:4px solid var(--quote-border);background:var(--soft);
  border-radius:0 8px 8px 0;color:#374151}
.content blockquote p{margin:.35em 0}
.content table{border-collapse:collapse;width:100%;margin:1.3em 0;font-size:15px}
.content th,.content td{border:1px solid var(--border);padding:8px 12px;text-align:left;vertical-align:top}
.content th{background:var(--soft);font-weight:600}
.content tr:nth-child(even) td{background:#fbfcfd}

/* 首图 / Hero */
.hero{
  background:linear-gradient(135deg,#4f46e5,#7c3aed);
  color:#fff;border-radius:14px;padding:30px 32px;margin-bottom:26px;
}
.hero h1{color:#fff;margin:0 0 .3em;font-size:32px}
.hero p{color:#e9e6ff;margin:.2em 0;font-size:16px}
.hero .tag{display:inline-block;background:rgba(255,255,255,.16);
  padding:3px 12px;border-radius:999px;font-size:13px;margin-bottom:10px}
.hero a{color:#fff;text-decoration:underline}

/* 页脚翻页 */
.pager{display:flex;justify-content:space-between;gap:14px;margin-top:42px;
  padding-top:20px;border-top:1px solid var(--border)}
.pager a{flex:1;padding:14px 16px;border:1px solid var(--border);border-radius:10px;
  color:var(--fg);font-size:14px}
.pager a:hover{background:var(--soft);text-decoration:none;border-color:var(--accent)}
.pager a .lbl{display:block;color:var(--muted);font-size:12px;margin-bottom:3px}
.pager a.next{text-align:right}
.pager a.empty{visibility:hidden}

.site-footer{border-top:1px solid var(--border);color:var(--muted);font-size:13px;
  text-align:center;padding:26px 20px}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin:1.4em 0}
.card{display:block;border:1px solid var(--border);border-radius:12px;padding:16px 18px;color:var(--fg)}
.card:hover{background:var(--soft);text-decoration:none;border-color:var(--accent)}
.card .num{color:var(--accent);font-weight:700;font-size:14px}
.card .t{font-weight:600;margin-top:4px;display:block}

@media(max-width:900px){
  .layout{display:block}
  .sidebar{position:static;width:auto;height:auto;border-right:none;
    border-bottom:1px solid var(--border);padding:14px 16px}
  .sidebar a{display:inline-block;margin:2px 4px}
  .content{padding:24px 18px 60px}
}
"""

# --------------------------------------------------------------------------
# 页面模板
# --------------------------------------------------------------------------
TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><!--TITLE--> · 学科视域</title>
<meta name="description" content="<!--DESC-->">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site-header">
  <span class="brand">学科视域<small>System</small></span>
  <span class="spacer"></span>
  <a class="top-link" href="index.html">首页</a>
  <a class="top-link" href="overview.html">总说</a>
  <a class="top-link" href="boundaries.html">边界清单</a>
</header>
<div class="layout">
  <aside class="sidebar">
<!--SIDEBAR-->
  </aside>
  <main class="content">
    <div class="content-inner">
<!--HERO-->
<!--BODY-->
<!--PAGER-->
    </div>
  </main>
</div>
<footer class="site-footer">学科视域 · 第二版 — 按世界自身的层次重排的通识底稿 · 文字采用 CC BY-SA 4.0</footer>
</body>
</html>"""

SIDEBAR_ITEM = '      <a href="{href}"{active}><span class="num">{num}</span>{title}</a>'


def sidebar_html(active_href):
    parts = ['      <a href="index.html"{a}>🏠 首页</a>'.format(
        a=' class="active"' if active_href == "index.html" else "")]
    parts.append('      <a href="overview.html"{a}>📖 总说</a>'.format(
        a=' class="active"' if active_href == "overview.html" else ""))
    parts.append('      <div class="nav-group">板块</div>')
    for n, title in SECTIONS:
        href = "section-%02d.html" % n
        a = ' class="active"' if href == active_href else ""
        parts.append(SIDEBAR_ITEM.format(href=href, active=a, num="%02d" % n, title=title))
    parts.append('      <div class="nav-group">工具</div>')
    parts.append('      <a href="boundaries.html"{a}>🔖 边界清单</a>'.format(
        a=' class="active"' if active_href == "boundaries.html" else ""))
    return "\n".join(parts)


def rewrite_links(html):
    # 形如 板块/01-xxx.md、../00-总说.md、02-世界由什么构成.md 等多种相对写法统一改写
    # 顺序很重要：先处理 00-总说，避免被下面的「数字前缀」规则误捕获成 section-00
    html = re.sub(r'(?<=href=")(?:\.\./|板块/)?00-总说\.md"', 'overview.html"', html)
    html = re.sub(r'(?<=href=")(?:\.\./|板块/)?边界清单\.md"', 'boundaries.html"', html)
    html = re.sub(r'(?<=href=")(?:\.\./|板块/)?README\.md"', 'index.html"', html)
    html = re.sub(r'(?<=href=")(?:\.\./|板块/)?LICENSE\.md"', 'LICENSE.html"', html)
    # 板块 NN（01-12）：无论链接里带不带标题，统一改写为 section-NN.html
    html = re.sub(r'(?<=href=")(?:\.\./|板块/)?(0[1-9]|1[0-2])-[^"]*?\.md"',
                  r'section-\1.html"', html)
    # 配图：../图/ 或 图/ -> 图/（所有页面扁平放在 docs/ 下）
    html = re.sub(r'(?<=src=")(?:\.\./)?图/', '图/', html)
    return html


def md_to_html(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    html = markdown(text, extensions=MD_EXT)
    return rewrite_links(html)


def render(title, body, active_href, desc="", hero="", pager=""):
    page = TPL
    page = page.replace("<!--TITLE-->", title)
    page = page.replace("<!--DESC-->", desc or title)
    page = page.replace("<!--SIDEBAR-->", sidebar_html(active_href))
    page = page.replace("<!--HERO-->", hero)
    page = page.replace("<!--BODY-->", body)
    page = page.replace("<!--PAGER-->", pager)
    return page


def pager_html(prev_, next_):
    parts = []
    if prev_ is None:
        parts.append('      <a class="empty"></a>')
    else:
        parts.append('      <a class="prev" href="%s"><span class="lbl">上一篇</span>%s</a>'
                     % (prev_[0], prev_[1]))
    if next_ is None:
        parts.append('      <a class="empty"></a>')
    else:
        parts.append('      <a class="next" href="%s"><span class="lbl">下一篇</span>%s</a>'
                     % (next_[0], next_[1]))
    return '    <nav class="pager">\n' + "\n".join(parts) + "\n    </nav>"


def main():
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(IMG_DST, exist_ok=True)

    # 样式
    with open(os.path.join(ASSETS, "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)

    # 复制配图
    img_src = os.path.join(ROOT, "图")
    if os.path.isdir(img_src):
        for fn in os.listdir(img_src):
            if fn.lower().endswith((".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp")):
                shutil.copy2(os.path.join(img_src, fn), os.path.join(IMG_DST, fn))

    # 首页 = README
    hero = ('    <div class="hero">\n'
            '      <span class="tag">通识底稿 · 约 13 万字</span>\n'
            '      <h1>学科视域（第二版）</h1>\n'
            '      <p>这里只回答两件事：这些东西为什么值得知道，以及它们究竟是什么。</p>\n'
            '      <p>按世界的层次重排的十二个板块 · <a href="overview.html">先读总说 →</a></p>\n'
            '    </div>')
    home = render("首页", md_to_html(os.path.join(ROOT, "README.md")),
                  "index.html", hero=hero)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(home)

    # 总说
    overview = render("总说", md_to_html(os.path.join(ROOT, "00-总说.md")),
                      "overview.html",
                      pager=pager_html(("index.html", "首页"), ("section-01.html", "01 如何描述世界")))
    with open(os.path.join(DOCS, "overview.html"), "w", encoding="utf-8") as f:
        f.write(overview)

    # 十二个板块 + 翻页
    chain = []
    chain.append(("overview.html", "总说"))
    for n, _ in SECTIONS:
        chain.append(("section-%02d.html" % n, "%02d" % n))
    chain.append(("boundaries.html", "边界清单"))
    chain.append(("index.html", "首页"))

    for i, (n, title) in enumerate(SECTIONS):
        href = "section-%02d.html" % n
        prev_ = chain[i]                              # 第一篇的上一篇是「总说」
        next_ = chain[i + 2]                          # 下一篇是下一板块或「边界清单」
        pager = pager_html(prev_, next_)
        body = md_to_html(os.path.join(ROOT, "板块", "%02d-%s.md" % (n, title)))
        page = render("%02d %s" % (n, title), body, href, pager=pager)
        with open(os.path.join(DOCS, href), "w", encoding="utf-8") as f:
            f.write(page)

    # 边界清单
    boundaries = render("边界清单", md_to_html(os.path.join(ROOT, "边界清单.md")),
                        "boundaries.html",
                        pager=pager_html(("section-12.html", "12 人如何一起做事"),
                                         ("index.html", "首页")))
    with open(os.path.join(DOCS, "boundaries.html"), "w", encoding="utf-8") as f:
        f.write(boundaries)

    # LICENSE（保留为网页，方便站内跳转）
    lic = render("许可", md_to_html(os.path.join(ROOT, "LICENSE.md")),
                 None, pager=pager_html(("index.html", "首页"), None))
    with open(os.path.join(DOCS, "LICENSE.html"), "w", encoding="utf-8") as f:
        f.write(lic)

    # 关闭 Jekyll（避免 _ 开头目录被忽略；本项目无下划线目录，但加上更稳）
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")

    # 概览
    n_html = len([x for x in os.listdir(DOCS) if x.endswith(".html")])
    print("生成完成：docs/ 下 %d 个 HTML 页面 + %d 张配图 + style.css" % (
        n_html, len(os.listdir(IMG_DST))))


if __name__ == "__main__":
    main()
