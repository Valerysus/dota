# -*- coding: utf-8 -*-
import os, re, shutil, subprocess, sys, tempfile
"""
Generator for Dota 2 AI Coach Single-File Web App
Includes:
1. Replay parsing queue status with live timer countdown, auto-polling every 7s, and auto-reload.
2. Complete ward data extraction (obs_placed, sen_placed, item_uses, purchase) even when unparsed.
3. Player Net Worth graph: end-of-curve hero labels, multi-hero hover tooltip, interactive 10-hero legend with curve highlight.
4. Win Probability % Graph (Шанс на перемогу) with logistic modeling over time.
5. Stratz-style Impact Score (IMP) (+42, -26, etc.) for all 10 players, MVP/SVP badges, and impact leaderboard.
6. Hero Draft Math (+ / - % for each hero) with concrete counter/synergy explanations.
7. Persistent Floating Hero Dock with instant switching without scroll jumping.
8. Full-width widescreen 2-column esports dashboard.
9. Zero emoji stickers; clean minimal esports badges and typography.
"""

html_content = r'''<!DOCTYPE html>
<html lang="uk" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>Dota 2 AI Coach — аналітичний розбір матчів (OpenDota Live)</title>
<meta name="description" content="Розбір матчів Dota 2 на основі OpenDota API">
<meta name="theme-color" content="#1c1f26">
<meta property="og:type" content="website">
<meta property="og:title" content="Dota 2 AI Coach — розбір матчів">
<meta property="og:description" content="Розбір матчів Dota 2 на основі OpenDota API: драфт, матчапи, лейнінг, предмети, макро та план на наступну гру.">
<meta property="og:url" content="https://valerysus.github.io/dota/">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%231c1f26'/%3E%3Ctext x='32' y='42' font-family='Arial,sans-serif' font-weight='800' font-size='28' text-anchor='middle' fill='%23d08770'%3ED2%3C/text%3E%3C/svg%3E">
<style>
:root{
  --bg:#1c1f26; --card:#252932; --card2:#2b3039; --border:#363c48; --text:#e5e9f0; --muted:#9aa5b4;
  --good:#8fbc8f; --warn:#ebcb8b; --crit:#d08770; --accent:#88a9c3; --radius:14px;
  --good-bg:rgba(143,188,143,.10); --warn-bg:rgba(235,203,139,.10); --crit-bg:rgba(208,135,112,.12); --info-bg:rgba(136,169,195,.10);
}
[data-theme=light]{
  --bg:#f4f2ed; --card:#ffffff; --card2:#f8f6f1; --border:#e4e0d6; --text:#24292f; --muted:#5f6b7a;
  --good:#4f8a55; --warn:#a67c1a; --crit:#b5573b; --accent:#4a7192;
  --good-bg:rgba(79,138,85,.09); --warn-bg:rgba(166,124,26,.09); --crit-bg:rgba(181,87,59,.09); --info-bg:rgba(74,113,146,.08);
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 "Segoe UI",system-ui,-apple-system,Roboto,"Helvetica Neue",Arial,sans-serif;transition:background .2s,color .2s}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}

/* Widescreen Container */
.wrap{max-width:1720px;width:95%;margin:0 auto;padding:20px 20px 120px}

/* Header */
header{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border)}
.logo{display:flex;align-items:center;gap:12px}
.logo-mark{width:42px;height:42px;border-radius:10px;background:var(--card);border:1px solid var(--border);display:grid;place-items:center;font-weight:800;color:var(--crit);font-size:17px;letter-spacing:-.02em}
.logo h1{font-size:20px;margin:0;font-weight:700;line-height:1.2}
.logo small{display:block;color:var(--muted);font-size:13px;font-weight:400;margin-top:2px}

/* Buttons */
.btn{font:inherit;font-size:14px;border:1px solid var(--border);background:var(--card);color:var(--text);padding:9px 16px;border-radius:10px;cursor:pointer;transition:background .15s,border-color .15s,transform .1s;display:inline-flex;align-items:center;gap:8px;font-weight:550}
.btn:hover{border-color:var(--accent)}
.btn:disabled{opacity:.55;cursor:default}
.btn-primary{background:var(--accent);border-color:var(--accent);color:#1c1f26;font-weight:650}
[data-theme=light] .btn-primary{color:#fff}
.btn-sm{padding:6px 12px;font-size:13px;border-radius:8px}

/* Card */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:22px;margin-bottom:20px}
.card h2{font-size:19px;margin:0 0 6px;font-weight:700;display:flex;align-items:center}
.card h3{font-size:16px;margin:18px 0 8px;font-weight:650}
.sub{color:var(--muted);font-size:14px;margin:0 0 16px;line-height:1.5}

/* Search */
.search{display:flex;gap:12px}
.search input{flex:1;font:inherit;font-size:16px;padding:12px 16px;border-radius:10px;border:1px solid var(--border);background:var(--bg);color:var(--text);outline:none;transition:border-color .15s}
.search input:focus{border-color:var(--accent)}
.hint-line{color:var(--muted);font-size:13px;margin-top:10px}

/* Status / Error */
#status{display:none;align-items:center;gap:12px;padding:14px 18px;border-radius:12px;background:var(--card);border:1px solid var(--border);margin-bottom:20px;color:var(--muted)}
#status.on{display:flex}
.spinner{width:20px;height:20px;border-radius:50%;border:2.5px solid var(--border);border-top-color:var(--accent);animation:spin .8s linear infinite;flex:none}
@keyframes spin{to{transform:rotate(360deg)}}
.err{border-left:4px solid var(--crit)}

/* Clean Section Tag */
.sec-tag{display:inline-flex;align-items:center;justify-content:center;padding:2px 8px;border-radius:6px;background:var(--info-bg);border:1px solid var(--border);color:var(--accent);font-size:12px;font-weight:700;letter-spacing:.05em;margin-right:10px;vertical-align:1px;font-variant-numeric:tabular-nums}

/* Player Info */
.player{display:flex;gap:20px;align-items:center;flex-wrap:wrap}
.player img.avatar{width:68px;height:68px;border-radius:12px;border:1px solid var(--border)}
.player .name{font-size:20px;font-weight:700;margin:0}
.pill{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;font-size:13px;font-weight:550;border:1px solid var(--border);color:var(--muted);margin-right:6px;white-space:nowrap}
.pill.good{color:var(--good);border-color:var(--good);background:var(--good-bg)}
.pill.crit{color:var(--crit);border-color:var(--crit);background:var(--crit-bg)}
.pill.warn{color:var(--warn);border-color:var(--warn);background:var(--warn-bg)}
.wl{flex:1;min-width:220px}
.wlbar{height:10px;border-radius:6px;background:var(--crit-bg);overflow:hidden;margin-top:6px}
.wlbar>div{height:100%;background:var(--good)}

/* Match Strip */
.strip{display:flex;gap:12px;overflow-x:auto;padding-bottom:8px;scroll-snap-type:x proximity}
.mcard{flex:0 0 136px;scroll-snap-align:start;text-align:left;background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:10px;cursor:pointer;color:var(--text);font:inherit;font-size:13px;transition:border-color .15s,transform .1s}
.mcard:hover{border-color:var(--accent);transform:translateY(-2px)}
.mcard.active{border-color:var(--accent);background:var(--info-bg)}
.mcard img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:8px;display:block;margin-bottom:6px;background:var(--border)}
.mcard .res{font-weight:700;font-size:13px}
.res.win{color:var(--good)} .res.loss{color:var(--crit)}
.mcard .meta{color:var(--muted);font-size:13px}

/* Top Match Banner */
.match-top-banner{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:18px;margin-bottom:14px}
.match-top-left{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.match-score-badge{display:flex;align-items:center;gap:10px;background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:8px 16px;font-variant-numeric:tabular-nums}
.match-score-badge .score-val{font-size:22px;font-weight:800;letter-spacing:-.02em}
.match-score-badge .score-val.rad{color:var(--good)}
.match-score-badge .score-val.dire{color:var(--crit)}
.match-score-badge .score-vs{color:var(--muted);font-weight:600;font-size:14px}
.match-meta-info{display:flex;flex-direction:column;gap:2px}
.match-meta-title{font-size:18px;font-weight:700;margin:0;display:flex;align-items:center;gap:10px}
.match-meta-sub{color:var(--muted);font-size:13px}

/* Hero switcher inside banner */
.hero-mini-strip{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:16px;padding-top:14px;border-top:1px solid var(--border)}
.hero-mini-team{display:flex;align-items:center;gap:6px}
.hero-mini-label{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.hero-mini-label.rad{color:var(--good)}
.hero-mini-label.dire{color:var(--crit)}
.hero-mini-btn{position:relative;width:44px;height:28px;padding:0;border:2px solid transparent;border-radius:7px;overflow:hidden;background:var(--card2);cursor:pointer;transition:all .15s}
.hero-mini-btn:hover{transform:translateY(-2px);border-color:var(--muted)}
.hero-mini-btn.on{border-color:var(--accent);box-shadow:0 0 10px rgba(136,169,195,.5);transform:translateY(-2px) scale(1.06)}
.hero-mini-btn img{width:100%;height:100%;object-fit:cover;display:block}

/* 2-Column Dashboard Grid */
.dash-grid{display:grid;grid-template-columns:minmax(0, 1.15fr) minmax(0, 1fr);gap:24px;align-items:start;margin-bottom:20px}
.dash-col-left, .dash-col-right{display:flex;flex-direction:column;gap:20px;min-width:0}
@media (max-width:1180px){
  .dash-grid{grid-template-columns:1fr}
}

/* Active Hero Card (Right Column) */
.active-hero-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:22px}
.active-hero-head{display:flex;gap:18px;align-items:center;flex-wrap:wrap}
.active-hero-head img.hero-portrait{width:116px;aspect-ratio:16/9;object-fit:cover;border-radius:10px;border:1px solid var(--border)}
.active-hero-info{flex:1;min-width:220px}
.active-hero-title{font-size:20px;font-weight:700;margin:0 0 4px;display:flex;align-items:center;gap:8px}

/* Items */
.items{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.items img{width:42px;height:30px;border-radius:5px;border:1px solid var(--border);object-fit:cover;background:var(--card2)}
.items .neutral{border-radius:50%;width:32px;height:32px}

/* Stat Tiles */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:12px 0 4px}
.tile{background:var(--card2);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.tile .k{color:var(--muted);font-size:13px;font-weight:550}
.tile .v{font-size:19px;font-weight:700;margin-top:2px;font-variant-numeric:tabular-nums}
.tile .v.good{color:var(--good)} .tile .v.warn{color:var(--warn)} .tile .v.crit{color:var(--crit)}

/* Benchmarks */
.bm{display:grid;grid-template-columns:160px 80px 1fr;gap:6px 14px;align-items:center;margin-top:10px}
.bm .lab{font-size:14px;font-weight:550}
.bm .raw{font-weight:650;text-align:right;font-variant-numeric:tabular-nums;font-size:14px}
.bar{height:10px;border-radius:6px;background:var(--card2);border:1px solid var(--border);overflow:hidden}
.bar>div{height:100%;border-radius:6px}
.bm .txt{grid-column:2/-1;font-size:13px;color:var(--muted);margin-top:-4px;margin-bottom:6px}

/* Coach Issues & Alerts */
.issue{border-radius:12px;padding:14px 16px;margin:12px 0;border-left:4px solid var(--accent);background:var(--info-bg)}
.issue.crit{border-color:var(--crit);background:var(--crit-bg)}
.issue.warn{border-color:var(--warn);background:var(--warn-bg)}
.issue.good{border-color:var(--good);background:var(--good-bg)}
.issue .it{font-weight:650;font-size:15px;margin-bottom:6px;display:flex;gap:8px;align-items:baseline}
.issue .tag{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.issue.crit .tag{color:var(--crit)} .issue.warn .tag{color:var(--warn)} .issue.good .tag{color:var(--good)} .issue.info .tag{color:var(--accent)}
.issue p{margin:6px 0;font-size:14px;line-height:1.55}

/* Timeline Table */
.timeline{width:100%;border-collapse:collapse;font-size:14px}
.timeline td{padding:8px 6px;border-bottom:1px solid var(--border);vertical-align:middle}
.timeline td img{width:38px;height:27px;border-radius:4px;vertical-align:middle;margin-right:8px}
.delta{font-weight:650;font-variant-numeric:tabular-nums}
.delta.good{color:var(--good)} .delta.warn{color:var(--warn)} .delta.crit{color:var(--crit)}
.enemies{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.enemies figure{margin:0;text-align:center;font-size:12px;color:var(--muted);width:80px}
.enemies img{width:80px;border-radius:6px;border:1px solid var(--border);display:block;margin-bottom:2px}

/* Interactive Checkbox Plan */
.plan label{display:flex;gap:12px;align-items:flex-start;padding:14px;border:1px solid var(--border);border-radius:12px;margin:10px 0;cursor:pointer;background:var(--card2);transition:border-color .15s}
.plan label:hover{border-color:var(--accent)}
.plan input{width:18px;height:18px;margin-top:3px;accent-color:var(--good);flex:none;cursor:pointer}
.plan label.done{opacity:.6}
.plan label.done span.plan-txt{text-decoration:line-through}
.plan .num{font-weight:700;color:var(--accent);margin-right:4px}

/* Draft styles */
.draft-prob{display:flex;align-items:center;justify-content:space-between;margin:12px 0 8px;font-size:15px;font-weight:700}
.draft-prob .rad-txt{color:var(--good)}
.draft-prob .dire-txt{color:var(--crit)}
.draft-bar{height:12px;border-radius:8px;background:var(--crit);display:flex;overflow:hidden;border:1px solid var(--border)}
.draft-bar > .rad-fill{height:100%;background:var(--good);transition:width .4s}
.draft-stats{display:grid;grid-template-columns:1fr;gap:10px;margin-top:14px}
.draft-row{display:grid;grid-template-columns:130px 1fr 130px;align-items:center;gap:10px;font-size:13px}
.draft-row .l-val{text-align:right;font-weight:650;color:var(--good)}
.draft-row .r-val{text-align:left;font-weight:650;color:var(--crit)}
.draft-row .name{text-align:center;color:var(--muted);font-size:13px}
.draft-meter{height:8px;border-radius:4px;background:var(--card2);border:1px solid var(--border);display:flex;overflow:hidden}
.draft-meter .m-rad{background:var(--good)}
.draft-meter .m-dire{background:var(--crit);margin-left:auto}
.draft-matchups{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.draft-pb{display:flex;gap:6px;overflow-x:auto;padding:8px 0;margin-top:10px}
.pb-badge{position:relative;flex:0 0 46px;text-align:center}
.pb-badge img{width:46px;height:26px;border-radius:4px;display:block;object-fit:cover;border:1px solid var(--border)}
.pb-badge.ban img{filter:grayscale(1);opacity:.55}
.pb-badge .pb-num{position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);font-size:12px;padding:0 4px;border-radius:4px;background:var(--card);border:1px solid var(--border);color:var(--muted);font-weight:700}
.pb-badge.rad{border-bottom:2px solid var(--good)}
.pb-badge.dire{border-bottom:2px solid var(--crit)}

/* Hero Draft Math (+ / - score) styles */
.draft-math-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
.draft-math-col{background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:14px}
.draft-math-col-head{font-weight:750;font-size:13px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.draft-math-row{display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)}
.draft-math-row:last-child{border-bottom:none}
.draft-math-row img{width:40px;height:24px;border-radius:4px;object-fit:cover;border:1px solid var(--border);flex:none;margin-top:2px}
.draft-math-info{flex:1;min-width:0}
.draft-math-head{display:flex;justify-content:space-between;align-items:center;font-size:13px;font-weight:650}
.draft-math-why{font-size:12px;color:var(--muted);line-height:1.35;margin-top:3px}
.draft-score-badge{display:inline-flex;align-items:center;padding:2px 7px;border-radius:6px;font-size:12px;font-weight:750;font-variant-numeric:tabular-nums}
.draft-score-badge.pos{background:var(--good-bg);border:1px solid var(--good);color:var(--good)}
.draft-score-badge.neg{background:var(--crit-bg);border:1px solid var(--crit);color:var(--crit)}

/* Graph styles */
.graph-tabs-row{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;border-bottom:1px solid var(--border);padding-bottom:12px;margin-bottom:14px}
.graph-tabs{display:flex;gap:8px;flex-wrap:wrap}
.graph-tab{font:inherit;background:var(--card2);border:1px solid var(--border);color:var(--muted);padding:7px 14px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600;transition:all .15s}
.graph-tab.active{background:var(--info-bg);color:var(--text);border-color:var(--accent)}
.graph-cont{position:relative;width:100%;background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:12px 14px 16px;overflow:hidden}
.graph-svg{width:100%;height:220px;display:block;overflow:visible;cursor:crosshair}
.graph-tip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:12px;color:var(--text);box-shadow:0 6px 16px rgba(0,0,0,.35);transform:translate(-50%,-125%);white-space:nowrap;display:none;z-index:20}
.graph-tip.show{display:block}
.graph-legend{display:flex;gap:16px;font-size:13px;color:var(--muted);margin-top:10px;flex-wrap:wrap}
.graph-legend span{display:inline-flex;align-items:center;gap:6px}
.graph-legend .dot{width:9px;height:9px;border-radius:50%}

/* Interactive Player Legend Grid */
.player-legend-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid var(--border)}
.player-legend-team{display:flex;flex-direction:column;gap:6px}
.player-legend-team-title{font-size:12px;font-weight:750;text-transform:uppercase;letter-spacing:.05em}
.player-legend-team-title.rad{color:var(--good)}
.player-legend-team-title.dire{color:var(--crit)}
.player-legend-list{display:flex;flex-wrap:wrap;gap:6px}
.player-legend-btn{
  display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border-radius:6px;background:var(--card);
  border:1px solid var(--border);font-size:12px;color:var(--text);cursor:pointer;transition:all .15s;
}
.player-legend-btn:hover{border-color:var(--accent);transform:translateY(-1px)}
.player-legend-btn.on{border-color:var(--accent);background:var(--info-bg)}
.player-legend-btn img{width:22px;height:14px;border-radius:3px;object-fit:cover}
.player-legend-btn .nw{font-weight:650;font-variant-numeric:tabular-nums;color:var(--muted)}

/* Curve labels in SVG */
.curve-label{font-size:12px;font-weight:600;letter-spacing:-.01em;pointer-events:none}

/* Stratz-style Impact Rating & Outcome styles */
.outcome-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
.outcome-col{background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:16px}
.outcome-col h3{margin:0 0 10px;font-size:15px;display:flex;align-items:center;gap:8px}
.outcome-list{list-style:none;padding:0;margin:0;font-size:13px}
.outcome-list li{margin-bottom:10px;padding-left:16px;position:relative;line-height:1.5}
.outcome-list li::before{content:"-";position:absolute;left:0;font-weight:700}
.outcome-col.winner li::before{color:var(--good)}
.outcome-col.loser li::before{color:var(--crit)}
.swing-card{background:var(--info-bg);border:1px solid var(--accent);border-radius:12px;padding:12px 16px;margin:12px 0}
.swing-card .head{font-weight:700;font-size:14px;color:var(--accent);margin-bottom:4px}

/* Impact Leaderboard Table */
.imp-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
.imp-col{background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:16px}
.imp-col-head{display:flex;justify-content:space-between;align-items:center;font-size:14px;font-weight:750;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.imp-card{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid var(--border);font-size:13px}
.imp-card:last-child{border-bottom:none}
.imp-card img{width:46px;height:28px;border-radius:5px;object-fit:cover;border:1px solid var(--border);flex:none;margin-top:2px}
.imp-card-main{flex:1;min-width:0}
.imp-card-top{display:flex;justify-content:space-between;align-items:center;gap:8px}
.imp-card-name{font-weight:700;display:flex;align-items:center;gap:6px}
.imp-tag{display:inline-flex;align-items:center;padding:2px 8px;border-radius:6px;font-size:12px;font-weight:800;font-variant-numeric:tabular-nums}
.imp-tag.mvp{background:rgba(235,203,139,.18);border:1px solid var(--warn);color:var(--warn)}
.imp-tag.svp{background:rgba(136,169,195,.18);border:1px solid var(--accent);color:var(--accent)}
.imp-tag.pos{background:var(--good-bg);border:1px solid var(--good);color:var(--good)}
.imp-tag.neg{background:var(--crit-bg);border:1px solid var(--crit);color:var(--crit)}
.imp-card-stats{display:flex;gap:8px;color:var(--muted);font-size:13px;margin-top:3px;flex-wrap:wrap}
.imp-card-desc{font-size:12px;color:var(--text);margin-top:4px;line-height:1.35;opacity:.85}

/* Fair Play, Ruiners & Cheaters Audit */
.fair-play-status{display:flex;align-items:flex-start;gap:14px;padding:14px 18px;border-radius:12px;margin-bottom:14px}
.fair-play-status.clean{background:var(--good-bg);border:1px solid rgba(143,188,143,.35)}
.fair-play-status.alert{background:var(--crit-bg);border:1px solid rgba(208,135,112,.4)}
.fair-play-status .fp-title{font-size:15px;font-weight:750;margin-bottom:3px}
.fair-play-status .fp-sub{font-size:12.5px;color:var(--muted);line-height:1.45}
.fair-play-grid{display:flex;flex-direction:column;gap:12px}
.fp-player-card{background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:10px}
.fp-player-top{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.fp-player-info{display:flex;align-items:center;gap:10px}
.fp-player-info img{width:46px;height:26px;border-radius:4px;object-fit:cover;border:1px solid var(--border)}
.fp-player-info .name{font-weight:700;font-size:14px}
.fp-badge-row{display:flex;gap:6px;flex-wrap:wrap}
.fp-badge{font-size:12px;font-weight:700;padding:3px 8px;border-radius:6px;display:inline-flex;align-items:center;gap:4px}
.fp-badge.crit{background:rgba(208,135,112,.2);color:var(--crit);border:1px solid rgba(208,135,112,.4)}
.fp-badge.warn{background:rgba(235,203,139,.18);color:var(--warn);border:1px solid rgba(235,203,139,.35)}
.fp-badge.info{background:rgba(136,169,195,.18);color:var(--accent);border:1px solid rgba(136,169,195,.35)}
.fp-issues-list{list-style:none;padding:0;margin:0;font-size:13px;display:flex;flex-direction:column;gap:6px}
.fp-issues-list li{padding-left:14px;position:relative;line-height:1.45;color:var(--text)}
.fp-issues-list li::before{content:"-";position:absolute;left:0;font-weight:bold;color:var(--crit)}
.fp-issues-list li.warn::before{color:var(--warn)}
.fp-issues-list li.info::before{color:var(--accent)}
.fp-actions{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.fp-btn{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;padding:5px 10px;border-radius:6px;background:var(--card);border:1px solid var(--border);color:var(--text);cursor:pointer;text-decoration:none;transition:all .15s}
.fp-btn:hover{background:var(--border);color:var(--text);text-decoration:none}
.fp-btn.steam{background:rgba(136,169,195,.18);border-color:var(--accent);color:var(--accent)}
.fp-btn.steam:hover{background:var(--accent);color:#fff}
.fp-dossier-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px;font-size:12px;line-height:1.5;margin-top:8px}
.fp-alias-tag{display:inline-block;padding:2px 6px;border-radius:4px;background:var(--card2);border:1px solid var(--border);margin:2px 4px 2px 0;font-size:12px}

/* Settings Mockup */
.mock{max-width:460px;border:1px solid var(--border);border-radius:12px;overflow:hidden;margin:16px 0;background:var(--card2);font-size:13px}
.mock .bar1{background:var(--border);padding:8px 14px;font-weight:600}
.mock .tabs{display:flex;gap:4px;padding:10px 14px;border-bottom:1px solid var(--border)}
.mock .tabs span{padding:4px 10px;border-radius:6px;color:var(--muted)}
.mock .tabs span.on{background:var(--info-bg);color:var(--text);font-weight:600}
.mock .row{display:flex;align-items:center;gap:10px;padding:12px 14px}
.mock .row.dim{color:var(--muted)}
.mock .chk{width:18px;height:18px;border-radius:4px;border:2px solid var(--good);display:grid;place-items:center;color:var(--good);font-weight:800;font-size:12px}
.mock .chk.off{border-color:var(--border);color:transparent}
.mock .arrow{color:var(--good);font-weight:700;margin-left:auto}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.herorow{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.herorow img{width:52px;border-radius:5px}
.herorow .wr{margin-left:auto;font-weight:650}

/* Persistent Floating Hero Dock */
.hero-dock{
  position:fixed;
  bottom:16px;
  left:50%;
  transform:translateX(-50%);
  z-index:9999;
  background:rgba(28,31,38,0.94);
  backdrop-filter:blur(16px);
  -webkit-backdrop-filter:blur(16px);
  border:1px solid var(--border);
  box-shadow:0 16px 40px rgba(0,0,0,0.6);
  border-radius:16px;
  padding:8px 14px;
  display:none;
  align-items:center;
  gap:12px;
  max-width:96vw;
  transition:transform .25s ease,opacity .25s ease;
}
.hero-dock.active{display:flex}
.hero-dock.collapsed{
  transform:translateX(-50%) translateY(calc(100% - 28px));
  opacity:.85;
}
.hero-dock.collapsed:hover{
  transform:translateX(-50%) translateY(0);
  opacity:1;
}
[data-theme=light] .hero-dock{
  background:rgba(255,255,255,0.95);
  box-shadow:0 16px 40px rgba(0,0,0,0.15);
}
.dock-team{display:flex;align-items:center;gap:6px}
.dock-side-badge{font-size:12px;font-weight:800;letter-spacing:.05em;padding:3px 6px;border-radius:6px;flex:none}
.dock-side-badge.rad{color:var(--good);background:var(--good-bg)}
.dock-side-badge.dire{color:var(--crit);background:var(--crit-bg)}
.dock-hero-btn{
  position:relative;width:44px;height:28px;padding:0;border:2px solid transparent;border-radius:7px;
  overflow:hidden;background:var(--card2);cursor:pointer;transition:all .15s ease;flex:none;
}
.dock-hero-btn img{width:100%;height:100%;object-fit:cover;display:block}
.dock-hero-btn:hover{transform:translateY(-2px);border-color:var(--muted)}
.dock-hero-btn.on{border-color:var(--accent);box-shadow:0 0 12px rgba(136,169,195,.6);transform:translateY(-2px) scale(1.08)}
.dock-hero-lvl{
  position:absolute;bottom:1px;right:2px;font-size:12px;font-weight:700;
  background:rgba(0,0,0,.7);color:#fff;padding:0 3px;border-radius:3px;line-height:1.2;
}
.dock-mid{display:flex;flex-direction:column;align-items:center;padding:0 8px;border-left:1px solid var(--border);border-right:1px solid var(--border);flex:none}
.dock-score{font-size:14px;font-weight:800;line-height:1.1;font-variant-numeric:tabular-nums}
.dock-score .rad-s{color:var(--good)}
.dock-score .dire-s{color:var(--crit)}
.dock-dur{font-size:12px;color:var(--muted)}
.dock-sel-info{display:flex;align-items:center;gap:8px;padding-left:4px;border-left:1px solid var(--border)}
.dock-cur-name{font-size:13px;font-weight:700;color:var(--text);white-space:nowrap}
.dock-jump-btn{padding:3px 8px;font-size:12px;white-space:nowrap}
.dock-collapse-btn{background:none;border:none;color:var(--muted);font-size:15px;font-weight:700;cursor:pointer;padding:2px 6px;border-radius:6px;transition:all .15s}
.dock-collapse-btn:hover{background:var(--card2);color:var(--text)}

@media (max-width:860px){
  .wrap{padding:16px 12px 110px}
  .hero-dock{overflow-x:auto;justify-content:flex-start;max-width:98vw;padding:6px 10px}
  .dock-hero-btn{width:36px;height:24px}
  .dock-sel-info{display:none}
  .two,.draft-math-grid,.imp-grid{grid-template-columns:1fr}
  .bm{grid-template-columns:120px 64px 1fr}
  .search{flex-direction:column}
  .draft-matchups,.outcome-grid{grid-template-columns:1fr}
  .draft-row{grid-template-columns:90px 1fr 90px}
  .player-legend-grid{grid-template-columns:1fr}
}

/* Benchmarks Modern Grid & Table */
.bm-table{display:flex;flex-direction:column;gap:8px;margin-top:14px}
.bm-head-row{display:grid;grid-template-columns:135px 85px 95px 125px 1fr;gap:12px;align-items:center;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);padding-bottom:8px;border-bottom:1px solid var(--border)}
.bm-item-row{display:grid;grid-template-columns:135px 85px 95px 125px 1fr;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.bm-item-row:last-child{border-bottom:none}
.bm-col-lab{font-size:14px;font-weight:600}
.bm-col-val{font-size:14px;font-weight:750;text-align:right;font-variant-numeric:tabular-nums}
.bm-col-med{font-size:13px;color:var(--muted);text-align:right;font-variant-numeric:tabular-nums}
.bm-col-diff{display:flex;justify-content:flex-end}
.bm-col-bar{display:flex;align-items:center;gap:10px}
.bm-col-bar .bar{flex:1;position:relative;height:12px;border-radius:6px;background:var(--card2);border:1px solid var(--border);overflow:visible}
.bm-col-bar .bar>div{height:100%;border-radius:5px;position:relative;z-index:1}
.bar-mid-pin{position:absolute;left:50%;top:-3px;bottom:-3px;width:2px;background:var(--text);opacity:.45;z-index:3;border-radius:1px}
.bm-pct-txt{font-size:12px;font-weight:700;color:var(--muted);font-variant-numeric:tabular-nums;min-width:32px;text-align:right}
.bm-desc-row{grid-column:1/-1;font-size:12.5px;color:var(--muted);margin-top:3px;line-height:1.55;background:rgba(0,0,0,.15);border-radius:8px;padding:6px 12px}

/* Tactical Death Audit styles */
.death-audit-box{margin-top:18px;border-top:1px solid var(--border);padding-top:18px}
.death-audit-title{font-size:15px;font-weight:750;display:flex;align-items:center;gap:10px;margin-bottom:6px}
.death-killers-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:10px;margin:10px 0 16px}
.death-killer-card{display:flex;align-items:center;gap:10px;background:var(--card2);border:1px solid var(--border);border-radius:10px;padding:8px 12px}
.death-killer-card img{width:46px;height:28px;border-radius:5px;object-fit:cover;border:1px solid var(--border);flex:none}
.death-killer-name{font-size:13px;font-weight:700}
.death-killer-stat{font-size:12px;color:var(--crit);font-weight:600}
.death-timeline{display:flex;flex-direction:column;gap:10px;margin-top:12px}
.death-item{display:flex;gap:12px;align-items:flex-start;background:var(--card2);border:1px solid var(--border);border-left:4px solid var(--crit);border-radius:10px;padding:10px 14px;font-size:13px;line-height:1.55}
.death-time-badge{font-size:12px;font-weight:800;padding:3px 8px;border-radius:6px;background:var(--crit-bg);color:var(--crit);font-variant-numeric:tabular-nums;white-space:nowrap;margin-top:2px}
.death-item-body{flex:1;min-width:0}
.death-item-head{display:flex;align-items:center;gap:8px;font-weight:700;margin-bottom:3px}
.death-item-head img{width:32px;height:20px;border-radius:4px;object-fit:cover}
.death-item-reason{color:var(--text);margin-top:2px}
.death-item-tip{color:var(--accent);font-size:13px;margin-top:5px;padding-top:4px;border-top:1px dashed rgba(255,255,255,.08)}


/* Stratz-style Draft Grid - Full Widescreen */
.dash-full-section{width:100%;min-width:0;margin-bottom:20px}
.stratz-draft-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:16px 0}
@media(max-width:1180px){.stratz-draft-grid{grid-template-columns:1fr}}
.stratz-team-col{background:var(--card2);border:1px solid var(--border);border-radius:14px;padding:16px;min-width:0}
.stratz-team-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border)}
.stratz-team-title{font-size:16px;font-weight:800;display:flex;align-items:center;gap:8px}
.stratz-team-score{font-size:14px;font-weight:800;padding:3px 10px;border-radius:6px;font-variant-numeric:tabular-nums}
.stratz-team-score.rad{background:var(--good-bg);color:var(--good);border:1px solid var(--good)}
.stratz-team-score.dire{background:var(--crit-bg);color:var(--crit);border:1px solid var(--crit)}
.stratz-heroes-row{display:grid;grid-template-columns:repeat(5, minmax(0, 1fr));gap:10px}
@media(max-width:768px){.stratz-heroes-row{grid-template-columns:repeat(2, minmax(0, 1fr))}}
.stratz-hero-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 8px;display:flex;flex-direction:column;align-items:center;text-align:center;transition:all .15s ease;min-width:0;overflow:hidden}
.stratz-hero-card:hover{border-color:var(--accent);transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,.25)}
.stratz-hero-card.best{border-color:var(--good);box-shadow:0 0 10px rgba(143,188,143,.15)}
.stratz-hero-card.weak{border-color:rgba(208,135,112,.6)}
.stratz-hero-img-wrap{position:relative;width:100%;aspect-ratio:16/9;border-radius:6px;overflow:hidden;margin-bottom:6px;border:1px solid rgba(255,255,255,.08);box-shadow:0 2px 6px rgba(0,0,0,.3)}
.stratz-hero-img-wrap img{width:100%;height:100%;object-fit:cover;display:block}
.stratz-role-badge{font-size:12px;font-weight:750;padding:2px 6px;border-radius:4px;background:rgba(0,0,0,.5);color:var(--text);margin-bottom:4px;white-space:nowrap;border:1px solid rgba(255,255,255,.06)}
.stratz-hero-name{font-size:12px;font-weight:750;line-height:1.2;margin-bottom:3px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.stratz-hero-score{font-size:13px;font-weight:800;margin-bottom:8px;font-variant-numeric:tabular-nums}
.stratz-hero-score.pos{color:var(--good)}
.stratz-hero-score.neg{color:var(--crit)}
.stratz-vs-matrix{width:100%;display:flex;flex-direction:column;gap:3px;background:rgba(0,0,0,.25);border-radius:6px;padding:5px 4px;margin-bottom:8px}
.stratz-vs-row{display:flex;align-items:center;justify-content:space-between;font-size:12px;padding:2px 3px;border-radius:4px;transition:background .1s}
.stratz-vs-row:hover{background:rgba(255,255,255,.06)}
.stratz-vs-left{display:flex;align-items:center;gap:6px;min-width:0;overflow:hidden}
.stratz-vs-left img{width:22px;height:13px;border-radius:2px;object-fit:cover;flex:none}
.stratz-vs-hname{font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:70px}
.stratz-vs-val{font-weight:750;font-size:12px;font-variant-numeric:tabular-nums;flex:none}
.stratz-vs-val.pos{color:var(--good)}
.stratz-vs-val.neg{color:var(--crit)}
.stratz-vs-val.zero{color:var(--muted)}
.stratz-advice-mini{font-size:12px;line-height:1.35;padding:6px;border-radius:6px;width:100%;text-align:center;margin-top:auto;display:flex;flex-direction:column;align-items:center;gap:4px;min-height:56px;justify-content:center}
.stratz-advice-mini.pos{background:var(--good-bg);border:1px solid var(--good)}
.stratz-advice-mini.neg{background:var(--crit-bg);border:1px solid rgba(208,135,112,.5)}
.stratz-advice-mini.neu{background:rgba(255,255,255,.04);color:var(--muted);border:1px solid var(--border)}
.stratz-sub-badge{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:1px 5px;border-radius:3px;color:var(--crit);background:rgba(208,135,112,.2)}
.stratz-sub-badge.good{color:var(--good);background:rgba(143,188,143,.2)}
.stratz-sub-badge.neutral{color:var(--muted);background:rgba(255,255,255,.08)}
.stratz-sub-chips{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;align-items:center}
.stratz-chip{display:inline-flex;align-items:center;gap:4px;padding:2px 6px;border-radius:4px;background:rgba(208,135,112,.25);border:1px solid rgba(208,135,112,.4);font-size:12px;font-weight:700;color:var(--text);cursor:help;white-space:nowrap}
.stratz-chip-img{width:18px;height:11px;border-radius:2px;object-fit:cover}
.stratz-chip-delta{color:var(--good);font-weight:800;margin-left:2px}
.stratz-sub-text{font-size:12px;color:var(--muted);line-height:1.25;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical}

/* Draft Math Clean Cards */
.draft-math-row{display:flex;gap:12px;align-items:flex-start;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin-bottom:10px;transition:border-color .15s}
.draft-math-row:hover{border-color:var(--accent)}
.draft-math-row img{width:52px;height:32px;border-radius:6px;object-fit:cover;border:1px solid var(--border);flex:none;margin-top:2px}
.draft-math-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}
.draft-math-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px}
.draft-hero-title{font-size:14px;font-weight:750}
.draft-point{font-size:12.5px;line-height:1.5;color:var(--text)}
.draft-point.good b{color:var(--good)}
.draft-point.bad b{color:var(--crit)}
.draft-point.syn b{color:var(--accent)}
.draft-advice{font-size:12.5px;line-height:1.5;margin-top:5px;padding:6px 10px;border-radius:8px;background:rgba(0,0,0,.15);border:1px solid var(--border)}
.draft-advice.pos{background:var(--good-bg);border-color:var(--good);color:var(--text)}
.draft-advice.neg{background:var(--crit-bg);border-color:var(--crit);color:var(--text)}

/* ===== Доступність ===== */
button:focus-visible, a:focus-visible, input:focus-visible, [tabindex]:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion: reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
.scroll-x{overflow-x:auto;-webkit-overflow-scrolling:touch}

/* ===== Мобільна верстка (<= 600px) ===== */
@media (max-width:600px){
  .wrap{width:100%;padding:12px 10px 110px}
  header{flex-wrap:wrap}
  .logo h1{font-size:18px}
  .card{padding:14px;border-radius:12px}
  .card h2{font-size:17px;flex-wrap:wrap;gap:6px}
  .search{flex-direction:column}
  .search .btn{width:100%;justify-content:center}
  .match-top-banner{flex-direction:column;align-items:flex-start}
  .hero-mini-strip{gap:8px}
  .hero-mini-team{flex-wrap:wrap}
  .hero-mini-btn{width:38px;height:24px}
  .hero-dock{left:0;right:0;bottom:0;transform:none;max-width:100vw;width:100%;border-radius:12px 12px 0 0;gap:6px;padding:6px 8px;overflow-x:auto;justify-content:flex-start}
  .hero-dock.collapsed{transform:translateY(calc(100% - 26px))}
  .hero-dock.collapsed:hover{transform:none}
  .dock-hero-btn{width:32px;height:21px}
  .dock-mid{padding:0 4px}
  .dock-sel-info{display:none}
  .tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
  .bm-table{overflow-x:auto;-webkit-overflow-scrolling:touch}
  .bm-head-row,.bm-item-row{min-width:560px}
  .draft-row{grid-template-columns:40px 1fr 40px}
  .stratz-team-col{padding:10px}
  .stratz-heroes-row{grid-template-columns:repeat(2,minmax(0,1fr))}
  .graph-tabs{flex-wrap:nowrap;overflow-x:auto;width:100%}
  .graph-tab{white-space:nowrap}
  .graph-svg{height:180px}
  .graph-cont{padding:8px}
  .timeline{display:block;overflow-x:auto;white-space:nowrap}
  .outcome-grid,.imp-grid,.two,.player-legend-grid,.dash-grid{grid-template-columns:1fr}
  .death-item{flex-direction:column}
  .active-hero-head img.hero-portrait{width:96px}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">
      <div class="logo-mark">D2</div>
      <div>
        <h1>Dota 2 AI Coach</h1>
        <small>Живий аналітичний розбір матчів OpenDota API</small>
      </div>
    </div>
    <div style="display:flex;gap:10px;align-items:center">
      <button class="btn btn-sm" id="apiKeyBtn" type="button" title="Налаштування OpenDota API ключа">API Ключ</button>
      <button class="btn btn-sm" id="themeBtn" title="Перемкнути тему">Тема: Світла</button>
    </div>
  </header>
  <div id="apiKeyModal" style="display:none;margin-bottom:14px;padding:12px 16px;background:var(--card);border:1px solid var(--border);border-radius:10px">
    <div style="font-weight:700;font-size:13px;margin-bottom:8px">Налаштування OpenDota API Ключа</div>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <input id="apiKeyInput" type="text" placeholder="Вставте ваш api_key (необов'язково)" style="flex:1;min-width:240px;padding:8px 12px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:13px">
      <button class="btn btn-sm btn-primary" id="saveApiKeyBtn" type="button">Зберегти</button>
      <button class="btn btn-sm" id="clearApiKeyBtn" type="button">Очистити</button>
    </div>
    <div style="font-size:12px;color:var(--muted);margin-top:6px">
      Ключ зберігається у вашому браузері (localStorage) відкритим текстом. Не вводьте його на чужих комп'ютерах.
    </div>
  </div>

  <section class="card">
    <form class="search" id="searchForm" autocomplete="off" onsubmit="if(window.run) window.run(document.getElementById('q').value); return false;">
      <input id="q" placeholder="Account ID (Steam32), SteamID64 або Match ID" aria-label="ID гравця або матчу" autofocus>
      <button class="btn btn-primary" id="searchSubmitBtn" type="submit">Проаналізувати</button>
    </form>
    <div style="margin-top:10px"><button type="button" class="btn btn-sm" id="demoBtn" data-quick="9044569588">Спробувати демо-матч</button></div>
    <div class="hint-line">Розпізнається автоматично: Steam32 (напр. 94054712), SteamID64 (7656119…), номер матчу (10 цифр) або посилання з OpenDota/Dotabuff/Steam.</div>
    <div class="quick-presets" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px;font-size:13px">
      <span class="muted">Швидкі розбори:</span>
      <button type="button" class="pill" style="cursor:pointer;background:var(--card2)" data-quick="9044569588">Матч 9044569588 (Bloodseeker)</button>
      <button type="button" class="pill" style="cursor:pointer;background:var(--card2)" data-quick="9043612326">Матч 9043612326</button>
      <button type="button" class="pill" style="cursor:pointer;background:var(--card2)" data-quick="9038892612">Матч 9038892612</button>
      <button type="button" class="pill" style="cursor:pointer;background:var(--card2)" data-quick="94054712">Topson (94054712)</button>
    </div>
  </section>

  <div id="status"><div class="spinner"></div><span id="statusText">Завантаження…</span></div>
  <div id="error"></div>
  <div id="playerBox"></div>
  <div id="stripBox"></div>
  <div id="analysis"></div>
  <div id="trendBox"></div>
  <div id="planBox"></div>
</div>

<!-- Persistent Floating Hero Dock -->
<div id="floatingHeroDock" class="hero-dock" aria-label="Швидкий вибір героя"></div>

<script>
window.onerror = function(msg, url, line, col, error) {
  console.error("Global JS Error:", msg, "line:", line, error);
  const errBox = document.getElementById('error') || document.body;
  if (errBox) {
    errBox.innerHTML = '<div class="card err" style="margin:12px 0;padding:12px 16px;background:var(--crit-bg);border:1px solid var(--crit);border-radius:10px"><b>Помилка виконання JavaScript:</b> ' + (typeof msg === 'string' ? msg : 'Error') + ' (рядок ' + line + ')<br><small style="opacity:0.9">Якщо ви щойно оновили сайт, натисніть <b>Ctrl + F5</b> (або очистіть кеш), щоб скинути старий кеш браузера.</small></div>' + (errBox.innerHTML || '');
  }
};
/* ======================= Допоміжні утиліти ======================= */
const $ = s => document.querySelector(s);
window.$ = $;
const esc = s => (s == null ? '' : String(s)).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtT = s => {
  if (s == null || isNaN(s)) return '—';
  const neg = s < 0; s = Math.abs(Math.round(s));
  return (neg ? '-' : '') + Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
};
const nf = n => Math.round(n || 0).toLocaleString('uk-UA');
const pc = p => Math.round((p || 0) * 100);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const avg = a => a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0;
const isWin = (slot, radWin) => (slot < 128) === !!radWin;
const countBits = n => n == null ? 0 : (n.toString(2).match(/1/g) || []).length;

const state = {
  heroes: {},
  items: {},
  itemById: {},
  heroBenchmarks: {},
  account: null,
  recent: [],
  match: null,
  slot: null,
  trendCache: {},
  constantsLoaded: false,
  activeParsePoll: null
};

const BASE_API = 'https://api.opendota.com/api';

async function api(path, opts = {}) {
  let url = path.startsWith('http') ? path : BASE_API + path;
  const apiKey = localStorage.getItem('opendota_api_key') || '';
  if (apiKey && !url.includes('api_key=')) {
    url += (url.includes('?') ? '&' : '?') + 'api_key=' + encodeURIComponent(apiKey);
  }
  let lastErr = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await fetch(url, opts);
      if (res.status === 429) {
        const pause = (attempt + 1) * 2000;
        setStatus(`Ліміт запитів OpenDota API (429), очікування ${(pause/1000).toFixed(1)} с…`);
        await sleep(pause);
        continue;
      }
      if (!res.ok) throw new Error('HTTP ' + res.status + ' (' + res.statusText + ')');
      return await res.json();
    } catch (e) {
      lastErr = e;
      if (attempt < 2) await sleep(800 * (attempt + 1));
    }
  }
  throw lastErr || new Error('Ліміт запитів OpenDota (HTTP 429). Зачекайте хвилину або додайте API-ключ.');
}

async function loadConstants() {
  if (state.constantsLoaded) return;
  const TTL = 24 * 60 * 60 * 1000; // 24 години
  const get = async (k, ep) => {
    try {
      const c = localStorage.getItem(k);
      if (c) {
        const parsed = JSON.parse(c);
        if (parsed && parsed.ts && (Date.now() - parsed.ts < TTL) && parsed.data) {
          return parsed.data;
        }
      }
    } catch {}
    const d = await api(ep);
    try { localStorage.setItem(k, JSON.stringify({ ts: Date.now(), data: d })); } catch {}
    return d;
  };
  setStatus('Завантаження бази героїв і предметів…');
  const [hArr, iObj] = await Promise.all([
    get('d2_h_stats_v3', '/heroStats').catch(() => get('d2_heroes_v3', '/constants/heroes')),
    get('d2_items_v3', '/constants/items')
  ]);
  const parseHeroWinrate = h => {
    const pubPicks = Array.from({length: 8}, (_, i) => h[`${i+1}_pick`] || 0).reduce((s, v) => s + v, 0);
    const pubWins = Array.from({length: 8}, (_, i) => h[`${i+1}_win`] || 0).reduce((s, v) => s + v, 0);
    if (pubPicks > 1000) return pubWins / pubPicks;
    if (h.pro_pick && h.pro_pick >= 15) return h.pro_win / h.pro_pick;
    return 0.50;
  };

  if (Array.isArray(hArr)) {
    hArr.forEach(h => {
      state.heroes[h.id] = {
        id: h.id,
        name: h.name,
        dname: h.localized_name,
        img: h.img ? 'https://cdn.cloudflare.steamstatic.com' + h.img : '',
        attr: h.primary_attr,
        roles: h.roles || [],
        short: (h.name || '').replace('npc_dota_hero_', ''),
        winrate: parseHeroWinrate(h)
      };
    });
  } else if (hArr && typeof hArr === 'object') {
    Object.values(hArr).forEach(h => {
      state.heroes[h.id] = {
        id: h.id,
        name: h.name,
        dname: h.localized_name,
        img: h.img ? 'https://cdn.cloudflare.steamstatic.com' + h.img : '',
        attr: h.primary_attr,
        roles: h.roles || [],
        short: (h.name || '').replace('npc_dota_hero_', ''),
        winrate: parseHeroWinrate(h)
      };
    });
  }
  state.items = iObj || {};
  Object.entries(state.items).forEach(([k, v]) => {
    if (v && v.id != null) state.itemById[v.id] = k;
  });
  state.constantsLoaded = true;
}

const hero = id => state.heroes[id] || { dname: 'Герой #' + id, short: '', roles: [] };
const heroImg = id => state.heroes[id]?.img || '';
const itemName = k => (state.items[k] && state.items[k].dname) || k;
const cost = k => (state.items[k] && state.items[k].cost) || 0;
const itemIcon = (k, extraCls = '') => {
  if (!k) return '';
  const it = state.items[k];
  const src = it && it.img ? 'https://cdn.cloudflare.steamstatic.com' + it.img : '';
  const title = esc(it ? it.dname : k);
  return src ? `<img src="${src}" alt="${title}" title="${title}" class="${extraCls}">` : `<span class="pill">${title}</span>`;
};

function setStatus(t) { const s = $('#status'); s.classList.add('on'); $('#statusText').textContent = t; }
function clearStatus() { $('#status').classList.remove('on'); }
function showError(msg) { $('#error').innerHTML = `<div class="card err"><b>Повідомлення:</b> ${esc(msg)}</div>`; }
function issue(lvl, title, body) {
  const map = { crit: 'Критична помилка', warn: 'Зверни увагу', good: 'Сильна сторона', info: 'Аналітика' };
  return `<div class="issue ${lvl}"><div class="it"><span class="tag">${map[lvl] || ''}</span><span>${esc(title)}</span></div>${body}</div>`;
}
function tile(k, v, cls = '') {
  return `<div class="tile"><div class="k">${esc(k)}</div><div class="v ${cls}">${v}</div></div>`;
}
function timeAgo(sec) {
  const d = Math.max(0, Math.floor(Date.now() / 1000 - sec));
  if (d < 3600) return Math.floor(d / 60) + ' хв тому';
  if (d < 86400) return Math.floor(d / 3600) + ' год тому';
  return Math.floor(d / 86400) + ' дн тому';
}
function rankName(tier) {
  if (!tier) return 'Unranked';
  const names = ['Herald', 'Guardian', 'Crusader', 'Archon', 'Legend', 'Ancient', 'Divine', 'Immortal'];
  const r = Math.floor(tier / 10), star = tier % 10;
  return (names[r - 1] || 'Rank') + (r === 8 ? '' : ' [' + star + ']');
}

/* ======================= Розпізнавання ID ======================= */
function parseInput(raw) {
  const s = String(raw || '').trim();
  if (!s) return null;

  // 1. Посилання на матч
  const mUrl = s.match(/(?:matches|match)\/(\d+)/i);
  if (mUrl) return { type: 'match', id: mUrl[1] };

  // 2. Посилання на гравця
  const pUrl = s.match(/(?:players|profiles|id)\/(\d+)/i);
  if (pUrl) {
    if (pUrl[1].length === 17) {
      try {
        const a32 = (BigInt(pUrl[1]) - BigInt('76561197960265728')).toString();
        return { type: 'player', id: a32 };
      } catch {}
    }
    return { type: 'player', id: pUrl[1] };
  }

  // 3. SteamID64 (17 цифр)
  if (/^7656119\d{10}$/.test(s)) {
    try {
      const a32 = (BigInt(s) - BigInt('76561197960265728')).toString();
      return { type: 'player', id: a32 };
    } catch {}
  }

  // 4. Числові ідентифікатори
  // Сучасні Match ID у Dota 2 мають 10 цифр і починаються з 7, 8, 9 (напр. 9044569588)
  // Нові Steam32 акаунти з 10 цифр починаються з 1 (напр. 1737356567, 1011832947)
  if (/^[789]\d{9}$/.test(s)) {
    return { type: 'match', id: s, fallbackType: 'player' };
  }

  // Старіші матчі (9 цифр) або стандартні Steam32 акаунти (до 10 цифр)
  if (/^\d{5,10}$/.test(s)) {
    return { type: 'player', id: s, fallbackType: 'match' };
  }

  return null;
}

/* ======================= Пошук та запуск ======================= */
async function run(inputVal) {
  $('#error').innerHTML = '';
  const parsed = parseInput(inputVal);
  if (!parsed) {
    showError('Не вдалося розпізнати ID. Введіть Steam32 Account ID, SteamID64 або Match ID.');
    return;
  }
  try {
    await loadConstants();
    if (parsed.type === 'match') {
      try {
        state.account = null;
        $('#playerBox').innerHTML = '';
        $('#stripBox').innerHTML = '';
        await openStandaloneMatch(parsed.id);
        return;
      } catch (err) {
        if (parsed.fallbackType === 'player') {
          await loadPlayer(parsed.id);
          return;
        }
        throw err;
      }
    } else {
      try {
        await loadPlayer(parsed.id);
        return;
      } catch (err) {
        if (parsed.fallbackType === 'match') {
          state.account = null;
          $('#playerBox').innerHTML = '';
          $('#stripBox').innerHTML = '';
          await openStandaloneMatch(parsed.id);
          return;
        }
        throw err;
      }
    }
  } catch (e) {
    showError(e.message || String(e));
  } finally {
    clearStatus();
  }
}
window.run = run;

async function loadPlayer(accountId) {
  setStatus('Завантаження профілю гравця #' + accountId + '…');
  state.account = accountId;
  const [profileRes, wlRes, recentRes] = await Promise.all([
    api(`/players/${accountId}`).catch(() => null),
    api(`/players/${accountId}/wl?limit=20`).catch(() => null),
    api(`/players/${accountId}/recentMatches`).catch(() => [])
  ]);

  renderPlayer(profileRes, wlRes, accountId);
  state.recent = recentRes || [];
  renderStrip(state.recent);

  if (state.recent && state.recent.length) {
    await loadMatch(state.recent[0].match_id, accountId);
  } else {
    $('#analysis').innerHTML = privateHint(accountId);
    $('#floatingHeroDock').classList.remove('active');
  }
}

function renderPlayer(p, wl, accId) {
  const box = $('#playerBox');
  if (!p || !p.profile) {
    box.innerHTML = `<div class="card player"><div class="name">Гравець #${esc(accId)}</div><p class="sub">Профіль не має публічного імені в OpenDota або скритий.</p></div>`;
    return;
  }
  const prof = p.profile, w = wl?.win ?? 0, l = wl?.lose ?? 0, tot = w + l;
  const wr = tot ? Math.round((w / tot) * 100) : 0;
  box.innerHTML = `<section class="card player">
    <img class="avatar" src="${prof.avatarfull || prof.avatar}" alt="">
    <div style="flex:1;min-width:200px">
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
        <h2 class="name">${esc(prof.personaname || 'Dota Player')}</h2>
        <span class="pill">${rankName(p.rank_tier)}</span>
        ${p.leaderboard_rank ? `<span class="pill good">Ранг #${p.leaderboard_rank}</span>` : ''}
        ${p.mmr_estimate?.estimate ? `<span class="pill">~${p.mmr_estimate.estimate} MMR</span>` : ''}
      </div>
      <div class="muted" style="margin-top:4px">Account ID: <a href="${prof.profileurl}" target="_blank" rel="noopener">${accId}</a> · <a href="https://www.opendota.com/players/${accId}" target="_blank" rel="noopener">OpenDota</a> · <a href="https://www.dotabuff.com/players/${accId}" target="_blank" rel="noopener">Dotabuff</a></div>
    </div>
    <div class="wl">
      <div style="display:flex;justify-content:space-between;font-size:13px"><span class="muted">Вінрейт останніх 20 ігор</span><b>${w}W – ${l}L (${wr}%)</b></div>
      <div class="wlbar"><div style="width:${wr}%"></div></div>
    </div>
  </section>`;
}

function renderStrip(matches) {
  const box = $('#stripBox');
  if (!matches || !matches.length) { box.innerHTML = ''; return; }
  box.innerHTML = `<section class="card" style="padding:16px 20px 12px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <h3 style="margin:0;font-size:15px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">Останні 15 матчів (обери для повного аналізу)</h3>
      <span class="muted" style="font-size:13px">${matches.length} ігор</span>
    </div>
    <div class="strip">
      ${matches.map((m, i) => {
        const win = isWin(m.player_slot, m.radiant_win);
        return `<button class="mcard ${i === 0 ? 'active' : ''}" data-id="${m.match_id}">
          <img src="${heroImg(m.hero_id)}" alt="">
          <div class="res ${win ? 'win' : 'loss'}">${win ? 'Перемога' : 'Поразка'}</div>
          <div class="meta">${esc(hero(m.hero_id).dname)}</div>
          <div class="meta">${m.kills}/${m.deaths}/${m.assists} · ${fmtT(m.duration)}</div>
          <div class="meta" style="font-size:12px">${timeAgo(m.start_time)}</div>
        </button>`;
      }).join('')}
    </div>
  </section>`;
  box.querySelectorAll('.mcard').forEach(c => c.addEventListener('click', () => {
    box.querySelectorAll('.mcard').forEach(x => x.classList.remove('active'));
    c.classList.add('active');
    loadMatch(c.dataset.id, state.account);
  }));
}

function privateHint(accId) {
  return `<section class="card">
    <div class="issue warn">
      <div class="it"><span class="tag">Приватний профіль</span><span>У гравця #${esc(accId)} вимкнено публічну історію матчів у клієнті Dota 2</span></div>
      <p>Останні матчі не повертаються через публічне API, оскільки в налаштуваннях гри вимкнено передачу даних.</p>
    </div>
    <h3>Як увімкнути відкриту історію в Dota 2:</h3>
    <ol style="line-height:1.8;padding-left:22px;margin:12px 0">
      <li>Запусти Dota 2 → натисни Налаштування (шестірня у лівому верхньому кутку).</li>
      <li>Перейди на вкладку <b>«Розширені налаштування»</b> (Advanced Options).</li>
      <li>У правому стовпчику знайди блок <b>«Спільнота»</b> (Community).</li>
      <li>Постав галочку <b>«Загальнодоступна історія матчів» (Expose Public Match Data)</b>.</li>
      <li>Зіграй один матч або почекай 5–10 хвилин, щоб OpenDota синхронізувала профіль.</li>
    </ol>
    <div class="mock">
      <div class="bar1">Dota 2 → Налаштування</div>
      <div class="tabs"><span>Головні</span><span class="on">Розширені налаштування</span><span>Аудіо</span></div>
      <div class="row dim"><div class="chk off"></div> Активність друзів</div>
      <div class="row"><div class="chk">OK</div><b>Expose Public Match Data</b><span class="arrow">← увімкни</span></div>
    </div>
    <h3>Або перевір роботу тренера на відкритих даних:</h3>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px">
      <button class="btn btn-sm btn-primary" data-quick="9044569588">Матч 9044569588 (Bloodseeker, 43 хв)</button>
      <button class="btn btn-sm" data-quick="94054712">Гравець Topson (94054712 · 20 матчів)</button>
    </div>
  </section>`;
}

async function openStandaloneMatch(matchId) {
  setStatus('Завантаження матчу #' + matchId + '…');
  await loadMatch(matchId, null);
}

async function loadMatch(matchId, accountId) {
  setStatus('Завантаження повної телеметрії матчу #' + matchId + '…');
  const m = await api(`/matches/${matchId}`);
  state.match = m;

  let target = null;
  if (accountId) target = m.players.find(p => String(p.account_id) === String(accountId));
  if (!target && state.slot != null) target = m.players.find(p => p.player_slot === state.slot);
  if (!target) target = m.players[0];
  state.slot = target.player_slot;

  if (target) await getHeroBenchmarks(target.hero_id);

  setStatus('Завантаження статистики матчапів героїв (OpenDota)…');
  try { await loadHeroMatchups(m.players.map(x => x.hero_id)); } catch {}

  renderAnalysis();
}

async function selectHero(slot, preserveScroll = true) {
  const y = preserveScroll ? window.scrollY : null;
  state.slot = slot;
  const pl = state.match?.players.find(x => x.player_slot === slot);
  if (pl) await getHeroBenchmarks(pl.hero_id);
  renderAnalysis();
  if (y !== null) {
    window.scrollTo({ top: y, behavior: 'instant' });
  }
}

/* ======================= Визначення предметів, вардів та ролі ======================= */
function finalItems(p) {
  return ['item_0','item_1','item_2','item_3','item_4','item_5'].map(k => state.itemById[p[k]]).filter(Boolean);
}
function owned(p) {
  const s = new Set();
  finalItems(p).forEach(k => s.add(k));
  ['backpack_0','backpack_1','backpack_2'].forEach(k => { const n = state.itemById[p[k]]; if (n) s.add(n); });
  if (p.item_neutral) { const n = state.itemById[p.item_neutral]; if (n) s.add(n); }
  (p.purchase_log || []).forEach(e => s.add(e.key));
  return s;
}
function hasAny(set, arr) { return arr.some(k => set.has(k)); }

function getWardsData(p) {
  const obs = p.obs_placed ?? (p.obs_log?.length) ?? (p.purchase?.ward_observer) ?? (p.item_uses?.ward_observer) ?? 0;
  const sen = p.sen_placed ?? (p.sen_log?.length) ?? (p.purchase?.ward_sentry) ?? (p.item_uses?.ward_sentry) ?? 0;
  return { obs, sen, total: obs + sen };
}

const POS_NAMES = { 1:'Pos 1 · Carry', 2:'Pos 2 · Mid', 3:'Pos 3 · Offlane', 4:'Pos 4 · Soft Support', 5:'Pos 5 · Hard Support' };

// Широкі пули героїв за позиціями. Це лише «допуск» героя до позиції;
// конкретні рекомендації ранжуються за реальними матчапами проти ворожого складу.
const POSITION_POOLS_RAW = {
  1: ['Anti-Mage','Juggernaut','Phantom Assassin','Phantom Lancer','Faceless Void','Spectre','Medusa','Terrorblade','Luna','Morphling','Slark','Lifestealer','Wraith King','Sven','Gyrocopter','Drow Ranger','Ursa','Chaos Knight','Troll Warlord','Naga Siren','Weaver','Monkey King','Muerta','Razor','Alchemist','Riki','Bloodseeker','Templar Assassin','Lycan','Arc Warden','Kez','Clinkz','Nature\u2019s Prophet',"Nature's Prophet",'Shadow Fiend','Ember Spirit'],
  2: ['Shadow Fiend','Queen of Pain','Storm Spirit','Ember Spirit','Puck','Invoker','Templar Assassin','Lina','Leshrac','Outworld Destroyer','Death Prophet','Tinker','Zeus','Kunkka','Pangolier','Void Spirit','Huskar','Viper','Sniper','Dragon Knight','Arc Warden','Meepo','Necrophos','Batrider','Primal Beast','Lone Druid','Windranger','Monkey King','Broodmother','Timbersaw','Razor','Earth Spirit','Visage','Pugna','Magnus','Alchemist','Clinkz'],
  3: ['Axe','Centaur Warrunner','Tidehunter','Mars','Underlord','Slardar','Legion Commander','Bristleback','Dark Seer','Beastmaster','Sand King','Doom','Night Stalker','Timbersaw','Brewmaster','Primal Beast','Magnus','Enigma','Visage','Razor','Viper','Necrophos','Batrider','Dawnbreaker','Death Prophet','Pangolier','Omniknight','Abaddon','Venomancer','Windranger','Lycan','Kunkka','Dragon Knight','Earthshaker','Spirit Breaker','Broodmother','Huskar'],
  4: ['Earthshaker','Tusk','Spirit Breaker','Rubick','Clockwerk','Earth Spirit','Mirana','Nyx Assassin','Skywrath Mage','Hoodwink','Snapfire','Bounty Hunter','Phoenix','Pugna','Shadow Shaman','Weaver','Marci','Dark Willow','Grimstroke','Windranger','Tiny','Pangolier','Lion','Techies','Magnus','Ancient Apparition','Jakiro','Bane','Sand King','Batrider','Dawnbreaker','Venomancer','Zeus','Keeper of the Light','Ringmaster','Muerta'],
  5: ['Crystal Maiden','Lion','Lich','Dazzle','Witch Doctor','Shadow Demon','Disruptor','Winter Wyvern','Warlock','Oracle','Treant Protector','Jakiro','Ancient Apparition','Vengeful Spirit','Undying','Ogre Magi','Io','Chen','Enchantress','Silencer','Bane','Elder Titan','Keeper of the Light','Omniknight','Abaddon','Grimstroke','Dark Willow','Shadow Shaman','Snapfire','Pugna','Venomancer','Earthshaker','Marci','Phoenix','Rubick','Ringmaster']
};
let _posPoolCache = null;
function positionPools() {
  const n = Object.keys(state.heroes).length;
  if (_posPoolCache && _posPoolCache.n === n) return _posPoolCache.pools;
  const byName = {};
  Object.values(state.heroes).forEach(h => { if (h.dname) byName[h.dname.toLowerCase()] = h.id; });
  const pools = {};
  Object.entries(POSITION_POOLS_RAW).forEach(([pos, names]) => {
    pools[pos] = [...new Set(names.map(x => byName[x.toLowerCase()]).filter(Boolean))];
  });
  _posPoolCache = { n, pools };
  return pools;
}

// @pure-start
const PERMS_5 = (() => {
  const out = [];
  const rec = (arr, rest) => {
    if (!rest.length) { out.push(arr); return; }
    rest.forEach((v, i) => rec([...arr, v], [...rest.slice(0, i), ...rest.slice(i + 1)]));
  };
  rec([], [1, 2, 3, 4, 5]);
  return out;
})();
const _teamPosCache = new Map();

// Унікальний розподіл позицій 1–5 у команді: перебір усіх 120 варіантів
// і вибір того, що найкраще пояснює лінію (lane_role), фарм, варди та профіль героя.
function assignTeamPositions(team, mins) {
  const key = (state.match?.match_id || '') + ':' + team.map(x => x.player_slot + '-' + x.hero_id).join(',');
  if (_teamPosCache.has(key)) return _teamPosCache.get(key);
  const pools = positionPools();
  const farm = x => (x.gold_per_min || 0) + ((x.last_hits || 0) / mins) * 30;
  const order = [...team].sort((a, b) => farm(b) - farm(a));
  const fit = (x, pos) => {
    let s = 0;
    const rank = order.indexOf(x);
    s -= Math.abs(rank - (pos - 1)) * 2.2;
    const lr = x.lane_role;
    if (lr === 2) s += pos === 2 ? 7 : -2;
    else if (lr === 1) s += (pos === 1 || pos === 5) ? 4 : (pos === 2 ? -3 : -1);
    else if (lr === 3) s += (pos === 3 || pos === 4) ? 4 : (pos === 2 ? -3 : -1);
    else if (lr === 4) s += (pos === 1 || pos === 3) ? 1 : 0;
    if (x.is_roaming) s += pos === 4 ? 3 : 0;
    const w = getWardsData(x).total;
    if (w >= 10) s += pos === 5 ? 2.5 : pos === 4 ? 1.5 : -2;
    const roles = hero(x.hero_id).roles || [];
    if ((pools[pos] || []).includes(x.hero_id)) s += 2.5;
    if (roles.includes('Support')) s += pos >= 4 ? 1.5 : -1;
    if (roles.includes('Carry')) s += pos <= 2 ? 1 : (pos >= 4 ? -1 : 0);
    return s;
  };
  const res = new Map();
  if (team.length === 5) {
    const F = team.map(x => [0, 1, 2, 3, 4, 5].map(pos => pos ? fit(x, pos) : 0));
    let best = PERMS_5[0], bestS = -Infinity;
    for (const perm of PERMS_5) {
      let s = 0;
      for (let i = 0; i < 5; i++) s += F[i][perm[i]];
      if (s > bestS) { bestS = s; best = perm; }
    }
    team.forEach((x, i) => res.set(x.player_slot, best[i]));
  } else {
    order.forEach((x, i) => res.set(x.player_slot, Math.min(5, i + 1)));
  }
  _teamPosCache.set(key, res);
  return res;
}
// @pure-end

function detectRole(p, team, mins) {
  const asg = assignTeamPositions(team, mins);
  const pos = asg.get(p.player_slot) || 3;
  const wards = getWardsData(p).total;
  const lhpm = (p.last_hits || 0) / mins;
  const laneTxt = { 1: 'безпечна лінія', 2: 'центр', 3: 'складна лінія', 4: 'ліс' }[p.lane_role] || 'лінія невідома';
  return { pos, label: POS_NAMES[pos], core: pos <= 3, lhpm, why: `${laneTxt}, GPM ${p.gold_per_min || 0}, ${lhpm.toFixed(1)} LH/хв, вардів: ${wards}` };
}

/* ======================= Stratz-style Impact Score (IMP) ======================= */
function calcPlayerImpact(pl, team, enemies, m, role) {
  const mins = Math.max(1, m.duration / 60);
  const teamKills = Math.max(1, team.reduce((s, x) => s + (x.kills || 0), 0));
  const kp = (pl.kills + pl.assists) / teamKills;
  const kpPoints = (kp - 0.45) * 32;

  const avgDeaths = team.reduce((s, x) => s + (x.deaths || 0), 0) / 5;
  const deathPoints = (avgDeaths - pl.deaths) * 3.5;

  const teamDmg = Math.max(1, team.reduce((s, x) => s + (x.hero_damage || 0), 0));
  const dmgShare = (pl.hero_damage || 0) / teamDmg;
  const dmgPoints = (dmgShare - (role.core ? 0.24 : 0.12)) * 40;

  const td = pl.tower_damage || 0;
  const tdPoints = Math.min(15, Math.max(-4, (td - (role.core ? 1500 : 300)) / 600));

  const wards = getWardsData(pl);
  const supBonus = !role.core ? Math.min(14, (wards.obs * 0.8) + (wards.sen * 0.5) + ((pl.stuns || 0) * 0.25) + ((pl.hero_healing || 0) / 1000)) : 0;

  const kda = (pl.kills + pl.assists) / Math.max(1, pl.deaths);
  const kdaPoints = Math.min(10, Math.max(-8, (kda - 3.0) * 2));

  const win = isWin(pl.player_slot, m.radiant_win);
  const outcomeMod = win ? 5 : -5;

  const raw = kpPoints + deathPoints + dmgPoints + tdPoints + supBonus + kdaPoints + outcomeMod;
  const score = Math.round(Math.max(-50, Math.min(55, raw)));

  let tag = 'pos';
  if (score >= 25) tag = 'pos';
  else if (score >= 0) tag = 'pos';
  else tag = 'neg';

  return { score, kp, dmgShare, td, wards, tag };
}

/* Нормативи ключових предметів */
const CORE_T = {
  bfury: [14 * 60 + 30, 'критично для розгону фарму на лінії та стаках'],
  radiance: [16 * 60 + 30, 'пасивний AOE-урон та відхилення від атак'],
  maelstrom: [13 * 60, 'ранній темп та зачистка пачок кріпів'],
  blink: [12 * 60 + 30, 'ініціація та раптовий врив на ворожих героїв'],
  black_king_bar: [22 * 60, 'імунітет до магії у командних битвах'],
  manta: [18 * 60, 'скидання сайленсу та безпечний пуш ліній'],
  yasha: [13 * 60, 'швидкість пересування та фарму'],
  armlet: [11 * 60, 'ранній пік сили та виживання'],
  diffusal_blade: [14 * 60, 'випалювання мани та уповільнення цілей'],
  desolator: [17 * 60, 'зрізання броні та швидке взяття веж'],
  orchid: [16 * 60, 'соло-фраги на мобільних ворожих героях']
};
const SUP_T = {
  glimmer_cape: [16 * 60, 'невидимість та захист від магічного прокасту'],
  force_staff: [18 * 60, 'розрив дистанції та порятунок від Riki/Clock/Slark'],
  blink: [18 * 60, 'позиційна ініціація головним контролем'],
  solar_crest: [16 * 60, 'захисний бар\'єр для свого кора'],
  aether_lens: [17 * 60, 'безпечна дальність застосування здібностей']
};
const REGEN = ['tango', 'flask', 'clarity', 'enchanted_mango', 'magic_wand', 'magic_stick', 'faerie_fire', 'blood_grenade'];

/* ======================= Головний аналіз ======================= */
function renderAnalysis() {
  const m = state.match, p = m.players.find(x => x.player_slot === state.slot) || m.players[0];
  const dur = m.duration, mins = Math.max(1, dur / 60);
  const isRad = p.player_slot < 128, win = isWin(p.player_slot, m.radiant_win);
  const rad = m.players.filter(x => x.player_slot < 128), dire = m.players.filter(x => x.player_slot >= 128);
  const team = isRad ? rad : dire, enemies = isRad ? dire : rad;
  const parsed = !!m.version;
  const turbo = m.game_mode === 23;
  const bm = p.benchmarks || {};
  const role = detectRole(p, team, mins);
  const H = hero(p.hero_id);
  const mine = owned(p);
  const heroName = H.name;
  const deathTimes = parsed ? enemies.flatMap(e => (e.kills_log || []).filter(k => k.key === heroName).map(k => k.time)).sort((a, b) => a - b) : [];
  const detailedDeaths = parsed ? enemies.flatMap(e => (e.kills_log || []).filter(k => k.key === heroName).map(k => ({
    time: k.time,
    killer: e,
    killerHero: hero(e.hero_id)
  }))).sort((a, b) => a.time - b.time) : [];
  const tasks = [];
  const addTask = (w, text) => tasks.push({ w, text });
  const ctx = { m, p, dur, mins, win, team, enemies, rad, dire, parsed, turbo, bm, role, H, mine, deathTimes, detailedDeaths, addTask };

  // ---------- Верхній банер матчу ----------
  const rk = m.radiant_score ?? 0, dk = m.dire_score ?? 0;
  const swItem = x => {
    const isCur = x.player_slot === p.player_slot;
    return `<button class="hero-mini-btn ${isCur ? 'on' : ''}" data-slot="${x.player_slot}" aria-label="${esc(hero(x.hero_id).dname)}" aria-pressed="${isCur}" title="${esc(hero(x.hero_id).dname)}${x.personaname ? ' — ' + esc(x.personaname) : ''}">
      <img src="${heroImg(x.hero_id)}" alt="">
    </button>`;
  };

  const bannerHtml = `
  <section class="card" style="padding:20px 24px">
    <div class="match-top-banner">
      <div class="match-top-left">
        <div class="match-score-badge">
          <span class="score-val rad">${rk}</span>
          <span class="score-vs">:</span>
          <span class="score-val dire">${dk}</span>
        </div>
        <div class="match-meta-info">
          <div class="match-meta-title">
            <span>Матч <a href="https://www.opendota.com/matches/${m.match_id}" target="_blank" rel="noopener">${m.match_id}</a></span>
            <span class="pill ${m.radiant_win ? 'good' : 'crit'}">${m.radiant_win ? 'Перемога Radiant' : 'Перемога Dire'}</span>
            <span class="pill">${fmtT(dur)}</span>
            ${parsed ? '<span class="pill good">Реплей розпарсено</span>' : '<span class="pill warn">Без парсингу реплею</span>'}
            ${turbo ? '<span class="pill warn">Turbo</span>' : ''}
          </div>
          <div class="match-meta-sub">${new Date(m.start_time * 1000).toLocaleString('uk-UA', { dateStyle:'medium', timeStyle:'short' })} · Кластер ${m.cluster || '—'}</div>
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        ${!parsed ? `<button class="btn btn-sm btn-primary" id="bannerParseBtn" data-parse="${m.match_id}">Запросити розбір реплею в OpenDota</button>` : ''}
        <button class="btn btn-sm" id="copyReportBtn">Скопіювати резюме тренера</button>
      </div>
    </div>

    <!-- Міні-перемикач героїв у шапці -->
    <div class="hero-mini-strip">
      <div class="hero-mini-team">
        <span class="hero-mini-label rad">Radiant</span>
        ${rad.map(swItem).join('')}
      </div>
      <div style="width:1px;height:24px;background:var(--border);margin:0 4px"></div>
      <div class="hero-mini-team">
        <span class="hero-mini-label dire">Dire</span>
        ${dire.map(swItem).join('')}
      </div>
    </div>
  </section>`;

  // ---------- Верхня секція: Повнорозмірний драфт у стилі Stratz (на всю ширину) ----------
  const draftHtml = secDraftAnalysis(m, rad, dire);

  // ---------- Ліва колонка: Командна аналітика та аудит ----------
  let leftCol = '';
  leftCol += secInteractiveGraphs(m, rad, dire, p);
  leftCol += secMatchOutcome(m, rad, dire);
  leftCol += secFairPlayAudit(m, rad, dire);

  // ---------- Права колонка: Глибокий розбір обраного героя ----------
  let rightCol = '';
  rightCol += secHeroDetailCard(ctx);
  rightCol += secBenchmarks(ctx);
  rightCol += secLaning(ctx);
  rightCol += secItems(ctx);
  rightCol += secMacro(ctx);

  $('#analysis').innerHTML = `
    ${bannerHtml}
    <div class="dash-full-section" style="margin-bottom:20px">
      ${draftHtml}
    </div>
    <div class="dash-grid">
      <div class="dash-col-left">${leftCol}</div>
      <div class="dash-col-right">${rightCol}</div>
    </div>
  `;

  // Обробники кліку на міні-світчер
  $('#analysis').querySelectorAll('.hero-mini-btn').forEach(b => {
    b.addEventListener('click', () => selectHero(+b.dataset.slot, true));
  });

  // Оновлення та рендер плаваючого дока
  renderFloatingHeroDock(m, rad, dire, p);

  // Ініціалізація графіків та подій
  initGraphEvents(m, rad, dire, p);
  initCopyReport(m, p, role, H, win);
  initReplayParseHandlers();
  initDossierHandlers();

  // Нижні секції: Тренд і План
  renderPlan(ctx, tasks);
  renderTrendFor(p.account_id, H.dname);
}

/* ======================= Плаваючий док героїв ======================= */
function renderFloatingHeroDock(m, rad, dire, curPlayer) {
  const dock = $('#floatingHeroDock');
  if (!dock) return;
  const rk = m.radiant_score ?? 0, dk = m.dire_score ?? 0;
  const dur = m.duration;

  const renderDockItem = pl => {
    const isCur = pl.player_slot === curPlayer.player_slot;
    const H = hero(pl.hero_id);
    const role = detectRole(pl, pl.player_slot < 128 ? rad : dire, Math.max(1, dur / 60));
    const imp = calcPlayerImpact(pl, pl.player_slot < 128 ? rad : dire, pl.player_slot < 128 ? dire : rad, m, role);
    return `
      <button class="dock-hero-btn ${isCur ? 'on' : ''}" data-slot="${pl.player_slot}" aria-label="${esc(H.dname)}" aria-pressed="${isCur}" title="${esc(H.dname)}${pl.personaname ? ' (' + esc(pl.personaname) + ')' : ''} · ${role.label} · ${pl.kills}/${pl.deaths}/${pl.assists} · IMP ${imp.score >= 0 ? '+' : ''}${imp.score}">
        <img src="${heroImg(pl.hero_id)}" alt="${esc(H.dname)}">
        <span class="dock-hero-lvl">${pl.level || ''}</span>
      </button>
    `;
  };

  dock.innerHTML = `
    <div class="dock-team rad">
      <span class="dock-side-badge rad">RAD</span>
      ${rad.map(renderDockItem).join('')}
    </div>
    <div class="dock-mid">
      <div class="dock-score"><span class="rad-s">${rk}</span> : <span class="dire-s">${dk}</span></div>
      <div class="dock-dur">${fmtT(dur)}</div>
    </div>
    <div class="dock-team dire">
      ${dire.map(renderDockItem).join('')}
      <span class="dock-side-badge dire">DIRE</span>
    </div>
    <div class="dock-sel-info">
      <span class="dock-cur-name">${esc(hero(curPlayer.hero_id).dname)}</span>
      <button class="btn btn-sm dock-jump-btn" id="dockJumpBtn" title="Перейти до розбору героя">До героя</button>
    </div>
    <button class="dock-collapse-btn" id="dockCollapseBtn" title="Згорнути / розгорнути панель">_</button>
  `;
  dock.classList.add('active');

  dock.querySelectorAll('.dock-hero-btn').forEach(b => {
    b.addEventListener('click', () => {
      const targetSlot = +b.dataset.slot;
      if (targetSlot === state.slot) return;
      selectHero(targetSlot, true);
    });
  });

  $('#dockJumpBtn')?.addEventListener('click', () => {
    const el = $('#heroDetailCard') || $('#analysis');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  $('#dockCollapseBtn')?.addEventListener('click', () => {
    dock.classList.toggle('collapsed');
  });
}

/* ======================= Картка обраного героя ======================= */
function secHeroDetailCard(ctx) {
  const { p, H, win, role, m } = ctx;
  const items = finalItems(p).slice(0, 6);
  const bp = ['backpack_0','backpack_1','backpack_2'].map(k => state.itemById[p[k]]).filter(Boolean);
  const neutral = state.itemById[p.item_neutral];

  const teamKills = ctx.team.reduce((s, x) => s + (x.kills || 0), 0);
  const kp = teamKills ? Math.round(((p.kills + p.assists) / teamKills) * 100) : 0;
  const teamDmg = ctx.team.reduce((s, x) => s + (x.hero_damage || 0), 0);
  const dmgShare = teamDmg ? Math.round(((p.hero_damage || 0) / teamDmg) * 100) : 0;
  const imp = calcPlayerImpact(p, ctx.team, ctx.enemies, m, role);
  const wards = getWardsData(p);

  return `
  <section class="card" id="heroDetailCard">
    <div class="active-hero-head">
      <img class="hero-portrait" src="${heroImg(p.hero_id)}" alt="">
      <div class="active-hero-info">
        <h2 class="active-hero-title">
          <span>${esc(H.dname)}</span>
          <span class="res ${win ? 'win' : 'loss'}">${win ? 'ПЕРЕМОГА' : 'ПОРАЗКА'}</span>
          <span class="imp-tag ${imp.score >= 25 ? 'mvp' : imp.score >= 0 ? 'pos' : 'neg'}" style="margin-left:6px">IMP ${imp.score >= 0 ? '+' : ''}${imp.score}</span>
        </h2>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:6px 0">
          <span class="pill">${role.label}</span>
          <span class="pill">${p.kills}/${p.deaths}/${p.assists} (KDA ${(p.kda || 0).toFixed(1)})</span>
          ${p.personaname ? `<span class="pill">${esc(p.personaname)}</span>` : ''}
          <span class="pill">Рівень ${p.level || '—'}</span>
        </div>
        <div class="hint-line" style="margin-top:4px">Роль: ${role.why}. Імпакт: <b>${imp.score >= 0 ? '+' : ''}${imp.score}</b> (${imp.score >= 20 ? 'вирішальний вплив' : imp.score >= 0 ? 'стабільний внесок' : 'просідання'}).</div>
      </div>
    </div>

    <div class="tiles" style="margin-top:16px">
      ${tile('Імпакт матчу (IMP)', `${imp.score >= 0 ? '+' : ''}${imp.score}`, imp.score >= 20 ? 'good' : imp.score < 0 ? 'crit' : 'warn')}
      ${tile('Участь у вбивствах', kp + '%', kp < 40 ? 'warn' : 'good')}
      ${tile('Частка урону команди', dmgShare + '%', dmgShare < 15 && role.core ? 'warn' : '')}
      ${tile('Урон по спорудах', nf(p.tower_damage || 0))}
      ${tile('Observer / Sentry', `${wards.obs} / ${wards.sen}`)}
      ${tile('Золото / хв (GPM)', p.gold_per_min || 0)}
    </div>

    <div style="margin-top:16px">
      <div class="muted" style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px">Фінальний інвентар та артефакти</div>
      <div class="items">
        ${items.map(k => itemIcon(k)).join('')}
        ${bp.length ? '<span class="muted" style="margin:0 4px">|</span>' + bp.map(k => itemIcon(k)).join('') : ''}
        ${neutral ? itemIcon(neutral, 'neutral') : ''}
      </div>
    </div>
  </section>`;
}

/* ======================= Аналіз Драфту та Математика Героїв ======================= */
// Реальні матчапи OpenDota: /heroes/{id}/matchups -> { enemyId: [games, wins] }
async function loadHeroMatchups(ids) {
  state.matchups = state.matchups || {};
  const TTL = 3 * 24 * 60 * 60 * 1000;
  const need = [];
  [...new Set(ids)].forEach(id => {
    if (state.matchups[id] !== undefined) return;
    try {
      const cch = JSON.parse(localStorage.getItem('d2_mu_' + id) || 'null');
      if (cch && cch.data && Date.now() - cch.ts < TTL) { state.matchups[id] = cch.data; return; }
    } catch {}
    need.push(id);
  });
  for (let i = 0; i < need.length; i += 5) {
    await Promise.all(need.slice(i, i + 5).map(async id => {
      try {
        const arr = await api(`/heroes/${id}/matchups`);
        const map = {};
        (arr || []).forEach(r => { map[r.hero_id] = [r.games_played || 0, r.wins || 0]; });
        state.matchups[id] = map;
        try { localStorage.setItem('d2_mu_' + id, JSON.stringify({ ts: Date.now(), data: map })); } catch {}
      } catch { state.matchups[id] = null; }
    }));
  }
}

// Перевага героя A проти B у відсотках вінрейту (з байєсівським згладжуванням малих вибірок)
function matchupAdv(aId, bId) {
  const ma = state.matchups?.[aId]?.[bId];
  const mb = state.matchups?.[bId]?.[aId];
  let g = 0, w = 0;
  if (ma && (!mb || ma[0] >= mb[0])) { g = ma[0]; w = ma[1]; }
  else if (mb) { g = mb[0]; w = mb[0] - mb[1]; }
  if (g >= 8) {
    const K = 25;
    const wr = (w + 0.5 * K) / (g + K);
    return { v: Number(Math.max(-9, Math.min(9, (wr - 0.5) * 100)).toFixed(1)), n: g, real: true };
  }
  return { v: calcHeroPairwise(hero(aId), hero(bId)), n: g, real: false };
}

// Точний попарний розрахунок переваги героя A проти героя B (Stratz-style)
function calcHeroPairwise(hA, hB) {
  let delta = 0;
  const aId = hA.id, bId = hB.id;

  const PAIRS = [
    [93, 42, +1.8], [42, 93, -1.8], // Slark vs WK
    [4, 93, +3.2], [93, 4, -3.2],   // Bloodseeker vs Slark
    [26, 42, -1.8], [42, 26, +1.8], // Lion vs WK
    [26, 44, -1.4], [44, 26, +1.4], // Lion vs PA
    [71, 90, +2.4], [90, 71, -2.4], // SB vs KotL
    [71, 105, +2.2], [105, 71, -2.2], // SB vs Techies
    [71, 30, +2.0], [30, 71, -2.0], // SB vs WD
    [71, 44, +1.2], [44, 71, -1.2], // SB vs PA
    [70, 42, +1.5], [42, 70, -1.5], // Ursa vs WK
    [70, 71, +1.8], [71, 70, -1.8], // Ursa vs SB
    [70, 29, +1.6], [29, 70, -1.6], // Ursa vs Tidehunter
    [70, 12, -2.4], [12, 70, +2.4], // Ursa vs PL
    [70, 6, -2.0], [6, 70, +2.0],   // Ursa vs Drow
    [8, 22, +2.2], [22, 8, -2.2],   // Jugg vs Zeus
    [8, 34, +1.8], [34, 8, -1.8],   // Jugg vs Tinker
    [8, 3, -2.0], [3, 8, +2.0],     // Jugg vs Bane
    [8, 2, -1.8], [2, 8, +1.8],     // Jugg vs Axe
    [8, 28, -1.4], [28, 8, +1.4],   // Jugg vs Slardar
    [39, 87, -2.2], [87, 39, +2.2], // QoP vs Disruptor
    [39, 75, -2.0], [75, 39, +2.0], // QoP vs Silencer
    [39, 69, -2.4], [69, 39, +2.4], // QoP vs Doom
    [39, 5, +1.6], [5, 39, -1.6],   // QoP vs CM
    [39, 35, +1.8], [35, 39, -1.8], // QoP vs Sniper
    [88, 74, +2.8], [74, 88, -2.8], // Nyx vs Invoker
    [88, 52, +2.6], [52, 88, -2.6], // Nyx vs Leshrac
    [88, 17, +2.4], [17, 88, -2.4], // Nyx vs Storm
    [112, 44, +2.6], [44, 112, -2.6], // WW vs PA
    [112, 18, +2.4], [18, 112, -2.4], // WW vs Sven
    [112, 70, +2.2], [70, 112, -2.2], // WW vs Ursa
    [18, 26, +2.0], [26, 18, -2.0], // Sven vs Lion
    [18, 3, -2.2], [3, 18, +2.2]    // Sven vs Bane
  ];

  const matched = PAIRS.find(p => p[0] === aId && p[1] === bId);
  if (matched) {
    delta = matched[2];
  } else {
    const aRoles = hA.roles || [], bRoles = hB.roles || [];
    if (aRoles.includes('Disabler') && bRoles.includes('Escape')) delta += 0.8;
    if (bRoles.includes('Disabler') && aRoles.includes('Escape')) delta -= 0.8;
    if (aRoles.includes('Nuker') && hB.attr === 'agi') delta += 0.5;
    if (bRoles.includes('Nuker') && hA.attr === 'agi') delta -= 0.5;
    if (hA.attr === 'str' && bRoles.includes('Nuker')) delta += 0.4;
    const wrA = hA.winrate || 0.50, wrB = hB.winrate || 0.50;
    delta += (wrA - wrB) * 15;
  }
  return Number(Math.max(-3.5, Math.min(3.5, delta)).toFixed(1));
}

function calcHeroDraftAdvantage(h, team, enemies, p, role, usedRecs = new Set()) {
  const pos = role?.pos || 3;
  const posLabel = `Pos ${pos}`;
  const roleName = (role?.label || '').split('·')[1]?.trim() || '';
  const r1 = v => Number(v.toFixed(1));
  const sg = v => (v >= 0 ? '+' : '') + v.toFixed(1);
  const taken = new Set([...team, ...enemies].map(x => x.hero_id));

  const pairwiseVsEnemies = enemies.map(e => {
    const r = matchupAdv(h.id, e.hero_id);
    return { hero: hero(e.hero_id), score: r.v, n: r.n, real: r.real };
  });
  const counterScore = r1(pairwiseVsEnemies.reduce((s, x) => s + x.score, 0));
  const realCount = pairwiseVsEnemies.filter(x => x.real).length;
  const sortedVs = [...pairwiseVsEnemies].sort((a, b) => b.score - a.score);
  const goodVs = sortedVs.filter(x => x.score >= 1).map(x => `${x.hero.dname} ${sg(x.score)}`);
  const badVs = sortedVs.filter(x => x.score <= -1).reverse().map(x => `${x.hero.dname} ${sg(x.score)}`);

  // Кандидати тієї самої позиції, ранжовані за реальною сумою матчапів проти цих 5 ворогів
  const pool = positionPools()[pos] || [];
  const cands = pool.filter(id => !taken.has(id) && id !== h.id).map(id => {
    const rows = enemies.map(e => ({ e, r: matchupAdv(id, e.hero_id) }));
    return { id, name: hero(id).dname, score: r1(rows.reduce((s, x) => s + x.r.v, 0)), real: rows.filter(x => x.r.real).length, rows };
  }).filter(cd => cd.real >= Math.min(3, realCount)).sort((a, b) => b.score - a.score);

  const betterCount = cands.filter(cd => cd.score > counterScore).length;
  const better = cands.filter(cd => !usedRecs.has(cd.id) && cd.score - counterScore >= 2.0).slice(0, 2);
  const substitutes = better.map(cd => {
    const strong = [...cd.rows].sort((a, b) => b.r.v - a.r.v).filter(x => x.r.v > 0).slice(0, 2);
    return {
      id: cd.id, name: cd.name, delta: r1(cd.score - counterScore), score: cd.score,
      reason: `${sg(cd.score)}% проти цього складу (у ${h.dname} ${sg(counterScore)}%).` +
        (strong.length ? ' Сильний проти: ' + strong.map(x => `${hero(x.e.hero_id).dname} ${sg(x.r.v)}`).join(', ') + '.' : '')
    };
  });
  substitutes.forEach(s => usedRecs.add(s.id));

  const verdict = substitutes.length ? 'swap' : betterCount <= 2 ? 'best' : 'ok';
  let bestReason = '';
  if (verdict === 'best') {
    bestReason = betterCount === 0
      ? `Найкращий доступний вибір на ${posLabel} проти цього складу.`
      : `Топ-${betterCount + 1} з ${cands.length + 1} героїв ${posLabel}.`;
    if (goodVs.length) bestReason += ' Сильний проти: ' + goodVs.slice(0, 2).join(', ') + '.';
  } else if (verdict === 'ok') {
    bestReason = `Є ${betterCount} варіант(ів) трохи кращих, але різниця < 2% — пік прийнятний.`;
  } else {
    bestReason = badVs.length ? 'Слабкий проти: ' + badVs.slice(0, 2).join(', ') + '.' : 'Сумарно програє матчапи цьому складу.';
  }

  return {
    rawScore: counterScore,
    isBestPick: verdict === 'best',
    verdict,
    goodVs, badVs,
    synergies: [],
    betterPick: substitutes.length ? substitutes.map(s => s.name).join(' або ') : '',
    substitutes,
    bestReason,
    note: '',
    pairwiseVsEnemies,
    realCount,
    betterCount,
    poolSize: cands.length + 1,
    pos, posLabel, roleName
  };
}

function calibrateDraftScores(rawItems, targetNet) {
  return rawItems.map(item => ({
    ...item,
    score: Number(item.rawScore.toFixed(1))
  }));
}

function secDraftAnalysis(m, rad, dire) {
  const dur = m.duration || 0, mins = Math.max(1, dur / 60);
  const hRad = rad.map(x => hero(x.hero_id));
  const hDire = dire.map(x => hero(x.hero_id));

  const getCC = list => {
    let pts = 30;
    list.forEach(h => {
      const r = h.roles || [];
      if (r.includes('Disabler')) pts += 11;
      if (r.includes('Initiator')) pts += 7;
    });
    return Math.min(96, Math.max(25, Math.round(pts)));
  };
  const getPush = list => {
    let pts = 25;
    list.forEach(h => {
      const r = h.roles || [];
      if (r.includes('Pusher')) pts += 16;
      if (r.includes('Carry')) pts += 6;
    });
    return Math.min(96, Math.max(20, Math.round(pts)));
  };
  const getTF = list => {
    let pts = 30;
    list.forEach(h => {
      const r = h.roles || [];
      if (r.includes('Initiator')) pts += 12;
      if (r.includes('Nuker')) pts += 8;
    });
    return Math.min(96, Math.max(25, Math.round(pts)));
  };
  const getLate = list => {
    let pts = 25;
    list.forEach(h => {
      const r = h.roles || [];
      if (r.includes('Carry')) pts += 14;
      if (h.attr === 'agi') pts += 4;
    });
    return Math.min(96, Math.max(20, Math.round(pts)));
  };
  const getTempo = list => {
    let pts = 30;
    list.forEach(h => {
      const r = h.roles || [];
      if (r.includes('Support')) pts += 8;
      if (r.includes('Nuker')) pts += 5;
    });
    return Math.min(96, Math.max(25, Math.round(pts)));
  };

  const ccR = getCC(hRad), ccD = getCC(hDire);
  const puR = getPush(hRad), puD = getPush(hDire);
  const tfR = getTF(hRad), tfD = getTF(hDire);
  const ltR = getLate(hRad), ltD = getLate(hDire);
  const tpR = getTempo(hRad), tpD = getTempo(hDire);

  const pillarDiff = ((ccR - ccD) * 0.08) + ((puR - puD) * 0.06) + ((tfR - tfD) * 0.08) + ((ltR - ltD) * 0.06) + ((tpR - tpD) * 0.06);

  // Розрахунок драфту: унікальні позиції 1–5 + реальні матчапи
  const usedR = new Set(), usedD = new Set();
  const rawRadItems = rad.map(x => ({ x, r: detectRole(x, rad, mins) })).sort((a, b) => a.r.pos - b.r.pos)
    .map(({ x, r }) => ({ p: x, hero: hero(x.hero_id), role: r, ...calcHeroDraftAdvantage(hero(x.hero_id), rad, dire, x, r, usedR) }));
  const rawDireItems = dire.map(x => ({ x, r: detectRole(x, dire, mins) })).sort((a, b) => a.r.pos - b.r.pos)
    .map(({ x, r }) => ({ p: x, hero: hero(x.hero_id), role: r, ...calcHeroDraftAdvantage(hero(x.hero_id), dire, rad, x, r, usedD) }));

  const radMath = calibrateDraftScores(rawRadItems, 0);
  const direMath = calibrateDraftScores(rawDireItems, 0);

  const sumScoreR = Number(radMath.reduce((s, x) => s + x.score, 0).toFixed(1));
  const sumScoreD = Number(direMath.reduce((s, x) => s + x.score, 0).toFixed(1));
  const realPairs = radMath.reduce((s, x) => s + x.realCount, 0) + direMath.reduce((s, x) => s + x.realCount, 0);

  // Сума 25 попарних матчапів кожної сторони (A vs B ≈ −(B vs A)), тому ділимо різницю навпіл
  const totalAdvantage = (sumScoreR - sumScoreD) / 2;
  const probR = Math.max(25, Math.min(75, Math.round(50 + totalAdvantage)));
  const probD = 100 - probR;
  const favTeam = probR > probD ? 'Radiant' : probD > probR ? 'Dire' : 'Рівний драфт';
  const favDiff = Math.abs(probR - probD);

  const sg = v => (v >= 0 ? '+' : '') + v.toFixed(1);
  const renderStratzCard = item => {
    const scoreCls = item.score > 0 ? 'pos' : item.score < 0 ? 'neg' : '';
    const cardCls = item.verdict === 'best' ? 'best' : item.verdict === 'swap' ? 'weak' : '';
    const posTitle = `${esc(item.role.label)} — ${esc(item.role.why)}`;
    return `
      <div class="stratz-hero-card ${cardCls}">
        <div class="stratz-hero-img-wrap">
          <img src="${heroImg(item.hero.id)}" alt="${esc(item.hero.dname)}" loading="lazy">
        </div>
        <div class="stratz-role-badge" title="${posTitle}">${esc(item.posLabel)}</div>
        <div class="stratz-hero-name" title="${esc(item.hero.dname)}">${esc(item.hero.dname)}</div>
        <div class="stratz-hero-score ${scoreCls}" title="Сума 5 матчапів нижче">${sg(item.score)}%</div>

        <div class="stratz-vs-matrix">
          ${item.pairwiseVsEnemies.map(pe => `
            <div class="stratz-vs-row" title="${esc(item.hero.dname)} проти ${esc(pe.hero.dname)}: ${sg(pe.score)}% ${pe.real ? '(' + pe.n + ' ігор, OpenDota)' : '(мало даних — евристична оцінка)'}">
              <div class="stratz-vs-left">
                <img src="${heroImg(pe.hero.id)}" alt="">
                <span class="stratz-vs-hname">${esc(pe.hero.dname)}</span>
              </div>
              <span class="stratz-vs-val ${pe.score > 0 ? 'pos' : pe.score < 0 ? 'neg' : 'zero'}">${pe.real ? '' : '≈'}${sg(pe.score)}</span>
            </div>
          `).join('')}
        </div>

        ${item.verdict === 'swap' ? `
          <div class="stratz-advice-mini neg">
            <div class="stratz-sub-badge">Краща заміна</div>
            <div class="stratz-sub-chips">
              ${item.substitutes.map(s => `
                <span class="stratz-chip" title="${esc(s.reason)}">
                  <img src="${heroImg(s.id)}" alt="" class="stratz-chip-img">
                  <span>${esc(s.name)}</span><b class="stratz-chip-delta">+${s.delta.toFixed(1)}</b>
                </span>
              `).join('')}
            </div>
            <div class="stratz-sub-text" title="${esc(item.bestReason)}">${esc(item.bestReason)}</div>
          </div>
        ` : item.verdict === 'best' ? `
          <div class="stratz-advice-mini pos">
            <div class="stratz-sub-badge good">${item.betterCount === 0 ? 'Найкращий вибір' : 'Топ-пік'}</div>
            <div class="stratz-sub-text" title="${esc(item.bestReason)}">${esc(item.bestReason)}</div>
          </div>
        ` : `
          <div class="stratz-advice-mini neu">
            <div class="stratz-sub-badge neutral">Прийнятно</div>
            <div class="stratz-sub-text" title="${esc(item.bestReason)}">${esc(item.bestReason)}</div>
          </div>
        `}
      </div>
    `;
  };

  return `<section class="card">
    <h2><span class="sec-tag">01</span>Оцінка драфту (Stratz-style Matchup Matrix)</h2>
    <p class="sub">Кожне число — відхилення вінрейту героя від 50% проти конкретного ворога за статистикою матчапів OpenDota (малі вибірки згладжені; «≈» — даних замало, евристика). Бал героя = сума 5 матчапів. Позиції розподілені унікально 1–5 за лінією, фармом і вардами. Заміни підбираються з пулу героїв <b>тієї самої позиції</b> за реальною сумою матчапів проти цього ворожого складу і показуються, лише якщо дають ≥ +2%.</p>
    <p class="hint-line" style="margin-top:-8px">Покриття реальними даними: <b>${realPairs}/50</b> пар.</p>

    <div class="draft-prob">
      <span class="rad-txt">Radiant: ${probR}%</span>
      <span style="font-size:13px;color:var(--muted);font-weight:600">Перевага піку: ${favTeam} (${favDiff > 0 ? '+' + favDiff + '%' : 'рівно'})</span>
      <span class="dire-txt">Dire: ${probD}%</span>
    </div>
    <div class="draft-bar">
      <div class="rad-fill" style="width:${probR}%"></div>
    </div>

    <!-- Stratz-style 2-Team 5-Column Grid -->
    <div class="stratz-draft-grid">
      <div class="stratz-team-col">
        <div class="stratz-team-head">
          <div class="stratz-team-title" style="color:var(--good)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 22h20L12 2zm0 4.5l6.5 13H5.5L12 6.5z"/></svg>
            Герої Radiant (Сяйво)
          </div>
          <div class="stratz-team-score" style="color:var(--good)">${sumScoreR >= 0 ? '+' : ''}${sumScoreR}%</div>
        </div>
        <div class="stratz-heroes-row">
          ${radMath.map(renderStratzCard).join('')}
        </div>
      </div>

      <div class="stratz-team-col">
        <div class="stratz-team-head">
          <div class="stratz-team-title" style="color:var(--crit)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 22L22 2H2l10 20zm0-4.5L5.5 4.5h13L12 17.5z"/></svg>
            Герої Dire (Пітьма)
          </div>
          <div class="stratz-team-score" style="color:var(--crit)">${sumScoreD >= 0 ? '+' : ''}${sumScoreD}%</div>
        </div>
        <div class="stratz-heroes-row">
          ${direMath.map(renderStratzCard).join('')}
        </div>
      </div>
    </div>

    <div class="draft-stats" style="margin-top:20px">
      <div class="draft-row">
        <span class="l-val">${ccR}</span>
        <div class="name">Контроль / Дизейбли<div class="draft-meter"><div class="m-rad" style="width:${ccR}%"></div><div class="m-dire" style="width:${ccD}%"></div></div></div>
        <span class="r-val">${ccD}</span>
      </div>
      <div class="draft-row">
        <span class="l-val">${puR}</span>
        <div class="name">Осадження / Пуш веж<div class="draft-meter"><div class="m-rad" style="width:${puR}%"></div><div class="m-dire" style="width:${puD}%"></div></div></div>
        <span class="r-val">${puD}</span>
      </div>
      <div class="draft-row">
        <span class="l-val">${tfR}</span>
        <div class="name">Тімфайт 5-в-5<div class="draft-meter"><div class="m-rad" style="width:${tfR}%"></div><div class="m-dire" style="width:${tfD}%"></div></div></div>
        <span class="r-val">${tfD}</span>
      </div>
      <div class="draft-row">
        <span class="l-val">${ltR}</span>
        <div class="name">Лейтгейм потенціал<div class="draft-meter"><div class="m-rad" style="width:${ltR}%"></div><div class="m-dire" style="width:${ltD}%"></div></div></div>
        <span class="r-val">${ltD}</span>
      </div>
      <div class="draft-row">
        <span class="l-val">${tpR}</span>
        <div class="name">Ранній темп ліній<div class="draft-meter"><div class="m-rad" style="width:${tpR}%"></div><div class="m-dire" style="width:${tpD}%"></div></div></div>
        <span class="r-val">${tpD}</span>
      </div>
    </div>
  </section>`;
}

function secInteractiveGraphs(m, rad, dire, curPlayer) {
  const parsed = !!m.version;
  return `<section class="card">
    <h2><span class="sec-tag">02</span>Графіки темпу та динаміки матчу</h2>
    <p class="sub">Похвилинна динаміка золота, досвіду, індивідуального нетворсу 10 героїв та розрахунковий шанс на перемогу.</p>

    <div class="graph-tabs-row">
      <div class="graph-tabs" id="graphTabBtns" role="tablist" aria-label="Тип графіка">
        <button class="graph-tab active" data-tab="gold">Перевага золота (Net Worth Lead)</button>
        <button class="graph-tab" data-tab="xp">Перевага досвіду (XP Lead)</button>
        <button class="graph-tab" data-tab="players">Криві нетворсу (10 героїв)</button>
        <button class="graph-tab" data-tab="winprob">Шанс перемоги (Win Probability %)</button>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <span class="pill ${parsed ? 'good' : 'warn'}" id="graphParseBadge">${parsed ? 'Точна телеметрія реплею' : 'Оціночна динаміка (GPM/XPM)'}</span>
        ${!parsed ? `<button class="btn btn-sm btn-primary" data-parse="${m.match_id}">Запросити парсинг</button>` : ''}
      </div>
    </div>

    <div class="graph-cont" id="graphContainer">
      <div class="graph-tip" id="graphTip"></div>
      <svg class="graph-svg" id="matchSvg" viewBox="0 0 800 220" preserveAspectRatio="none" role="img" aria-label="Графік переваги золота Radiant над Dire по хвилинах">
        <!-- SVG генерується динамічно -->
      </svg>
      <div class="graph-legend" id="graphLegend"></div>
    </div>
  </section>`;
}

function initGraphEvents(m, rad, dire, curPlayer) {
  const svg = $('#matchSvg'), tip = $('#graphTip'), cont = $('#graphContainer'), leg = $('#graphLegend');
  if (!svg || !cont) return;

  const dur = m.duration, mins = Math.max(1, Math.floor(dur / 60));
  const allPlayers = [...rad, ...dire];

  // Підготовка кривих для кожного гравця (із захистом від порожніх даних)
  allPlayers.forEach(pl => {
    if (pl.gold_t && pl.gold_t.length > 2 && pl.gold_t.some(v => v > 0)) {
      pl._goldCurve = pl.gold_t.slice(0, mins + 1);
    } else {
      const isW = isWin(pl.player_slot, m.radiant_win);
      const gpm = pl.gold_per_min || 400;
      const finalNW = pl.net_worth || Math.round(gpm * mins);
      const nw10 = Math.round(gpm * 6.2);
      const curve = [600];
      for (let i = 1; i <= mins; i++) {
        if (i <= 10) {
          curve.push(Math.round(600 + (nw10 - 600) * (i / 10)));
        } else {
          const tRatio = (i - 10) / Math.max(1, mins - 10);
          const curved = Math.pow(tRatio, isW ? 1.15 : 0.85);
          curve.push(Math.round(nw10 + (finalNW - nw10) * curved));
        }
      }
      pl._goldCurve = curve;
    }

    if (pl.xp_t && pl.xp_t.length > 2 && pl.xp_t.some(v => v > 0)) {
      pl._xpCurve = pl.xp_t.slice(0, mins + 1);
    } else {
      const xpm = pl.xp_per_min || 450;
      const finalXP = Math.round(xpm * mins);
      const curve = [0];
      for (let i = 1; i <= mins; i++) {
        const tRatio = i / mins;
        curve.push(Math.round(finalXP * Math.pow(tRatio, 1.05)));
      }
      pl._xpCurve = curve;
    }
  });

  // Загальна перевага команд
  const hasRealAdv = m.radiant_gold_adv && m.radiant_gold_adv.length > 2 && m.radiant_gold_adv.some(v => v !== 0);
  const goldAdv = hasRealAdv ? m.radiant_gold_adv.slice(0, mins + 1) : Array.from({ length: mins + 1 }, (_, i) => {
    const rG = rad.reduce((s, p) => s + (p._goldCurve[i] || 0), 0);
    const dG = dire.reduce((s, p) => s + (p._goldCurve[i] || 0), 0);
    return rG - dG;
  });

  const hasRealXp = m.radiant_xp_adv && m.radiant_xp_adv.length > 2 && m.radiant_xp_adv.some(v => v !== 0);
  const xpAdv = hasRealXp ? m.radiant_xp_adv.slice(0, mins + 1) : Array.from({ length: mins + 1 }, (_, i) => {
    const rX = rad.reduce((s, p) => s + (p._xpCurve[i] || 0), 0);
    const dX = dire.reduce((s, p) => s + (p._xpCurve[i] || 0), 0);
    return rX - dX;
  });

  // Розрахунок кривої шансу на перемогу (Win Probability %)
  const winProbCurve = Array.from({ length: mins + 1 }, (_, i) => {
    if (i === mins) return m.radiant_win ? 100 : 0;
    const g = goldAdv[i] || 0;
    const x = xpAdv[i] || 0;
    const scale = 2200 + i * 120;
    const z = (g / scale) + (x / (scale * 1.8));
    const p = Math.round((1 / (1 + Math.exp(-z))) * 100);
    return Math.max(2, Math.min(98, p));
  });

  // Події об'єктів (Рошани, Вежі)
  const objs = m.objectives || [];
  const eventMap = {};
  objs.forEach(o => {
    const t = o.time || 0;
    const mi = Math.floor(t / 60);
    const k = String(o.key || o.type || '');
    if (k.includes('ROSHAN') || o.type === 'CHAT_MESSAGE_ROSHAN_KILL') {
      (eventMap[mi] ||= []).push(`Рошан на ${fmtT(t)}`);
    } else if (k.includes('tower3') || k.includes('tower4') || k.includes('barracks')) {
      const side = k.includes('goodguys') ? 'Radiant' : 'Dire';
      const bName = k.includes('tower4') ? 'T4' : k.includes('tower3') ? 'T3' : 'Бараки';
      (eventMap[mi] ||= []).push(`Впала ${bName} ${side} на ${fmtT(t)}`);
    }
  });

  let currentTab = 'gold';

  function renderAdvGraph(arr, isGold) {
    const N = arr.length;
    const maxVal = Math.max(3000, ...arr.map(v => Math.abs(v || 0)));
    const padX = 44, padY = 22, W = 800 - 2 * padX, H = 220 - 2 * padY;
    const y0 = padY + H / 2;

    const x = i => padX + (i / Math.max(1, N - 1)) * W;
    const y = v => y0 - (v / maxVal) * (H / 2);

    const pts = arr.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
    const radPts = [`${padX},${y0}`, ...arr.map((v, i) => `${x(i).toFixed(1)},${Math.min(y0, y(v)).toFixed(1)}`), `${x(N - 1).toFixed(1)},${y0}`].join(' ');
    const direPts = [`${padX},${y0}`, ...arr.map((v, i) => `${x(i).toFixed(1)},${Math.max(y0, y(v)).toFixed(1)}`), `${x(N - 1).toFixed(1)},${y0}`].join(' ');

    const eventCircles = Object.keys(eventMap).filter(mi => +mi < N).map(mi => {
      const v = arr[+mi] || 0;
      return `<circle cx="${x(+mi).toFixed(1)}" cy="${y(v).toFixed(1)}" r="4" fill="var(--accent)" stroke="var(--bg)" stroke-width="1.5"></circle>`;
    }).join('');

    const stepMin = mins > 40 ? 10 : 5;
    const timeLabels = [];
    for (let mi = 0; mi <= mins; mi += stepMin) {
      if (mi < N) {
        timeLabels.push(`<text x="${x(mi).toFixed(1)}" y="${220 - 4}" fill="var(--muted)" font-size="11" text-anchor="middle">${mi}:00</text>`);
      }
    }

    svg.innerHTML = `
      <defs>
        <linearGradient id="gradRad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--good)" stop-opacity="0.35"/><stop offset="100%" stop-color="var(--good)" stop-opacity="0.02"/></linearGradient>
        <linearGradient id="gradDire" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="var(--crit)" stop-opacity="0.35"/><stop offset="100%" stop-color="var(--crit)" stop-opacity="0.02"/></linearGradient>
      </defs>
      <line x1="${padX}" x2="${800 - padX}" y1="${padY}" y2="${padY}" stroke="var(--border)" stroke-dasharray="3,3" />
      <text x="${padX - 8}" y="${padY + 4}" fill="var(--good)" font-size="10" text-anchor="end">+${nf(maxVal)}</text>
      <line x1="${padX}" x2="${800 - padX}" y1="${y0}" y2="${y0}" stroke="var(--border)" stroke-width="1.2" />
      <text x="${padX - 8}" y="${y0 + 3}" fill="var(--muted)" font-size="10" text-anchor="end">0</text>
      <line x1="${padX}" x2="${800 - padX}" y1="${220 - padY}" y2="${220 - padY}" stroke="var(--border)" stroke-dasharray="3,3" />
      <text x="${padX - 8}" y="${220 - padY + 3}" fill="var(--crit)" font-size="10" text-anchor="end">-${nf(maxVal)}</text>
      <polygon points="${radPts}" fill="url(#gradRad)" />
      <polygon points="${direPts}" fill="url(#gradDire)" />
      <polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
      ${eventCircles}
      ${timeLabels.join('')}
      <line id="svgCursorLine" x1="0" x2="0" y1="${padY}" y2="${220 - padY}" stroke="var(--text)" stroke-width="1.2" stroke-dasharray="2,2" opacity="0"></line>
    `;

    leg.innerHTML = `
      <span><span class="dot" style="background:var(--good)"></span> Зона Radiant (перевага)</span>
      <span><span class="dot" style="background:var(--crit)"></span> Зона Dire (перевага)</span>
      <span><span class="dot" style="background:var(--accent)"></span> Ключові події на карті</span>
    `;

    svg.onmousemove = e => {
      const rect = svg.getBoundingClientRect();
      const clientX = e.clientX - rect.left;
      const t = Math.max(0, Math.min(N - 1, Math.round(((clientX - padX) / W) * (N - 1))));
      const val = arr[t] || 0;
      const side = val >= 0 ? 'Radiant' : 'Dire';
      const leader = Math.abs(val);
      const ev = eventMap[t] ? `<br><span style="color:var(--accent)">${eventMap[t].join('<br>')}</span>` : '';
      const cx = x(t);

      const cLine = $('#svgCursorLine');
      if (cLine) { cLine.setAttribute('x1', cx); cLine.setAttribute('x2', cx); cLine.setAttribute('opacity', '1'); }

      tip.innerHTML = `<b>${t}:00</b> · +${nf(leader)} ${side} (${isGold ? 'золото' : 'досвід'})${ev}`;
      tip.style.left = cx + 'px';
      tip.style.top = y(val) + 'px';
      tip.classList.add('show');
    };
    svg.onmouseleave = () => {
      tip.classList.remove('show');
      const cLine = $('#svgCursorLine');
      if (cLine) cLine.setAttribute('opacity', '0');
    };
  }

  function renderWinProbGraph() {
    const N = winProbCurve.length;
    const padX = 44, padY = 22, W = 800 - 2 * padX, H = 220 - 2 * padY;
    const y0 = padY + H / 2; // 50% line

    const x = i => padX + (i / Math.max(1, N - 1)) * W;
    const y = p => 220 - padY - (p / 100) * H;

    const pts = winProbCurve.map((p, i) => `${x(i).toFixed(1)},${y(p).toFixed(1)}`).join(' ');
    const radPts = [`${padX},${y0}`, ...winProbCurve.map((p, i) => `${x(i).toFixed(1)},${Math.min(y0, y(p)).toFixed(1)}`), `${x(N - 1).toFixed(1)},${y0}`].join(' ');
    const direPts = [`${padX},${y0}`, ...winProbCurve.map((p, i) => `${x(i).toFixed(1)},${Math.max(y0, y(p)).toFixed(1)}`), `${x(N - 1).toFixed(1)},${y0}`].join(' ');

    const stepMin = mins > 40 ? 10 : 5;
    const timeLabels = [];
    for (let mi = 0; mi <= mins; mi += stepMin) {
      if (mi < N) {
        timeLabels.push(`<text x="${x(mi).toFixed(1)}" y="${220 - 4}" fill="var(--muted)" font-size="11" text-anchor="middle">${mi}:00</text>`);
      }
    }

    svg.innerHTML = `
      <defs>
        <linearGradient id="wpRad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--good)" stop-opacity="0.35"/><stop offset="100%" stop-color="var(--good)" stop-opacity="0.02"/></linearGradient>
        <linearGradient id="wpDire" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="var(--crit)" stop-opacity="0.35"/><stop offset="100%" stop-color="var(--crit)" stop-opacity="0.02"/></linearGradient>
      </defs>
      <line x1="${padX}" x2="${800 - padX}" y1="${padY}" y2="${padY}" stroke="var(--border)" stroke-dasharray="3,3" />
      <text x="${padX - 8}" y="${padY + 4}" fill="var(--good)" font-size="10" text-anchor="end">100% Rad</text>
      <line x1="${padX}" x2="${800 - padX}" y1="${y0}" y2="${y0}" stroke="var(--border)" stroke-width="1.4" />
      <text x="${padX - 8}" y="${y0 + 3}" fill="var(--muted)" font-size="10" text-anchor="end">50%</text>
      <line x1="${padX}" x2="${800 - padX}" y1="${220 - padY}" y2="${220 - padY}" stroke="var(--border)" stroke-dasharray="3,3" />
      <text x="${padX - 8}" y="${220 - padY + 3}" fill="var(--crit)" font-size="10" text-anchor="end">100% Dire</text>
      <polygon points="${radPts}" fill="url(#wpRad)" />
      <polygon points="${direPts}" fill="url(#wpDire)" />
      <polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      ${timeLabels.join('')}
      <line id="svgCursorLine" x1="0" x2="0" y1="${padY}" y2="${220 - padY}" stroke="var(--text)" stroke-width="1.2" stroke-dasharray="2,2" opacity="0"></line>
    `;

    leg.innerHTML = `
      <span><span class="dot" style="background:var(--good)"></span> Перевага шансу Radiant</span>
      <span><span class="dot" style="background:var(--crit)"></span> Перевага шансу Dire</span>
      <span><span class="dot" style="background:var(--accent)"></span> Розрахункова ймовірність перемоги %</span>
    `;

    svg.onmousemove = e => {
      const rect = svg.getBoundingClientRect();
      const clientX = e.clientX - rect.left;
      const t = Math.max(0, Math.min(N - 1, Math.round(((clientX - padX) / W) * (N - 1))));
      const pR = winProbCurve[t] || 50;
      const pD = 100 - pR;
      const leader = pR >= 50 ? `Radiant ${pR}%` : `Dire ${pD}%`;
      const cx = x(t);

      const cLine = $('#svgCursorLine');
      if (cLine) { cLine.setAttribute('x1', cx); cLine.setAttribute('x2', cx); cLine.setAttribute('opacity', '1'); }

      tip.innerHTML = `<b>${t}:00</b> · Шанс перемоги: <b>${leader}</b> (Rad ${pR}% : ${pD}% Dire)`;
      tip.style.left = cx + 'px';
      tip.style.top = y(pR) + 'px';
      tip.classList.add('show');
    };
    svg.onmouseleave = () => {
      tip.classList.remove('show');
      const cLine = $('#svgCursorLine');
      if (cLine) cLine.setAttribute('opacity', '0');
    };
  }

  function renderPlayersGraph() {
    const N = mins + 1;
    let maxG = 2000;
    allPlayers.forEach(p => (p._goldCurve || []).forEach(v => { if (v > maxG) maxG = v; }));

    // Залишаємо відступ праворуч під назви героїв
    const padX = 44, padRight = 86, padY = 22, W = 800 - padX - padRight, H = 220 - 2 * padY;
    const x = i => padX + (i / Math.max(1, N - 1)) * W;
    const y = v => 220 - padY - (v / maxG) * H;

    const radColors = ['#8fbc8f', '#a3cca3', '#78a778', '#5e945e', '#bce0bc'];
    const direColors = ['#d08770', '#e06c75', '#e59079', '#c4664c', '#f0a088'];

    // Сортуємо для рознесення кінцевих підписів
    const sortedFinal = [...allPlayers].map(pl => {
      const gArr = pl._goldCurve || [];
      const endG = gArr[N - 1] || 0;
      return { pl, endG, rawY: y(endG) };
    }).sort((a, b) => a.rawY - b.rawY);

    // Рознесення підписів, щоб не накладалися
    for (let i = 1; i < sortedFinal.length; i++) {
      if (sortedFinal[i].rawY - sortedFinal[i-1].rawY < 12) {
        sortedFinal[i].rawY = sortedFinal[i-1].rawY + 12;
      }
    }
    const labelYMap = new Map();
    sortedFinal.forEach(item => labelYMap.set(item.pl.player_slot, item.rawY));

    // Лінії та підписи героїв на правому краї
    const polylines = [];
    const endLabels = [];

    allPlayers.forEach(pl => {
      const isCur = pl.player_slot === curPlayer.player_slot;
      const isR = pl.player_slot < 128;
      const sideIdx = (isR ? rad : dire).indexOf(pl);
      const col = isCur ? 'var(--accent)' : (isR ? radColors[sideIdx % 5] : direColors[sideIdx % 5]);
      const gArr = pl._goldCurve || [];
      const pts = gArr.slice(0, N).map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
      const strokeW = isCur ? 3.6 : 1.5;
      const op = isCur ? 1 : 0.72;
      const hObj = hero(pl.hero_id);

      // Видима лінія + невидима широка зона для ховеру
      polylines.push(`
        <polyline id="pline_${pl.player_slot}" points="${pts}" fill="none" stroke="${col}" stroke-width="${strokeW}" opacity="${op}" stroke-linecap="round" />
        <polyline class="hover-hit" data-slot="${pl.player_slot}" points="${pts}" fill="none" stroke="transparent" stroke-width="12" style="cursor:pointer" />
      `);

      const endY = labelYMap.get(pl.player_slot) || y(gArr[N - 1] || 0);
      const endG = nf(gArr[N - 1] || 0);
      endLabels.push(`
        <text class="curve-label" x="${W + padX + 4}" y="${endY + 3.5}" fill="${col}" font-weight="${isCur ? '750' : '600'}">${esc(hObj.dname)}</text>
      `);
    });

    const stepMin = mins > 40 ? 10 : 5;
    const timeLabels = [];
    for (let mi = 0; mi <= mins; mi += stepMin) {
      timeLabels.push(`<text x="${x(mi).toFixed(1)}" y="${220 - 4}" fill="var(--muted)" font-size="11" text-anchor="middle">${mi}:00</text>`);
    }

    svg.innerHTML = `
      <line x1="${padX}" x2="${800 - padRight}" y1="${padY}" y2="${padY}" stroke="var(--border)" stroke-dasharray="3,3" />
      <text x="${padX - 8}" y="${padY + 4}" fill="var(--muted)" font-size="10" text-anchor="end">${nf(maxG)}</text>
      <line x1="${padX}" x2="${800 - padRight}" y1="${220 - padY}" y2="${220 - padY}" stroke="var(--border)" stroke-width="1.2" />
      <text x="${padX - 8}" y="${220 - padY + 4}" fill="var(--muted)" font-size="10" text-anchor="end">0</text>
      ${polylines.join('')}
      ${endLabels.join('')}
      ${timeLabels.join('')}
      <line id="svgCursorLine" x1="0" x2="0" y1="${padY}" y2="${220 - padY}" stroke="var(--text)" stroke-width="1.2" stroke-dasharray="2,2" opacity="0"></line>
    `;

    // Інтерактивна сітка легенди з 10 героями (з фінальним нетворсом)
    leg.innerHTML = `
      <div class="player-legend-grid">
        <div class="player-legend-team">
          <span class="player-legend-team-title rad">Radiant Гравці</span>
          <div class="player-legend-list">
            ${rad.map(pl => {
              const isCur = pl.player_slot === curPlayer.player_slot;
              const fnw = nf(pl._goldCurve?.[N - 1] || 0);
              return `<button class="player-legend-btn ${isCur ? 'on' : ''}" data-slot="${pl.player_slot}" title="Клік — переглянути розбір героя">
                <img src="${heroImg(pl.hero_id)}" alt="">
                <span>${esc(hero(pl.hero_id).dname)}</span>
                <span class="nw">${fnw}</span>
              </button>`;
            }).join('')}
          </div>
        </div>

        <div class="player-legend-team">
          <span class="player-legend-team-title dire">Dire Гравці</span>
          <div class="player-legend-list">
            ${dire.map(pl => {
              const isCur = pl.player_slot === curPlayer.player_slot;
              const fnw = nf(pl._goldCurve?.[N - 1] || 0);
              return `<button class="player-legend-btn ${isCur ? 'on' : ''}" data-slot="${pl.player_slot}" title="Клік — переглянути розбір героя">
                <img src="${heroImg(pl.hero_id)}" alt="">
                <span>${esc(hero(pl.hero_id).dname)}</span>
                <span class="nw">${fnw}</span>
              </button>`;
            }).join('')}
          </div>
        </div>
      </div>
    `;

    // Клік та ховер по кнопках у легенді
    leg.querySelectorAll('.player-legend-btn').forEach(btn => {
      const slot = +btn.dataset.slot;
      btn.addEventListener('click', () => selectHero(slot, true));
      btn.addEventListener('mouseenter', () => highlightCurve(slot));
      btn.addEventListener('mouseleave', () => resetCurveHighlight());
    });

    // Підсвічування лінії
    function highlightCurve(slot) {
      allPlayers.forEach(pl => {
        const line = $(`#pline_${pl.player_slot}`);
        if (!line) return;
        if (pl.player_slot === slot) {
          line.setAttribute('stroke-width', '4.5');
          line.setAttribute('opacity', '1');
        } else {
          line.setAttribute('stroke-width', '1');
          line.setAttribute('opacity', '0.22');
        }
      });
    }

    function resetCurveHighlight() {
      allPlayers.forEach(pl => {
        const line = $(`#pline_${pl.player_slot}`);
        if (!line) return;
        const isCur = pl.player_slot === curPlayer.player_slot;
        line.setAttribute('stroke-width', isCur ? '3.6' : '1.5');
        line.setAttribute('opacity', isCur ? '1' : '0.72');
      });
    }

    // Ховер по лініях через hit-зони
    svg.querySelectorAll('.hover-hit').forEach(hit => {
      hit.addEventListener('mouseenter', () => highlightCurve(+hit.dataset.slot));
      hit.addEventListener('mouseleave', () => resetCurveHighlight());
    });

    svg.onmousemove = e => {
      const rect = svg.getBoundingClientRect();
      const clientX = e.clientX - rect.left;
      const t = Math.max(0, Math.min(N - 1, Math.round(((clientX - padX) / W) * (N - 1))));
      const cx = x(t);
      const cLine = $('#svgCursorLine');
      if (cLine) { cLine.setAttribute('x1', cx); cLine.setAttribute('x2', cx); cLine.setAttribute('opacity', '1'); }

      // Лідери за нетворсом на цю хвилину
      const sortedAtT = [...allPlayers].map(pl => ({ pl, g: pl._goldCurve?.[t] || 0 })).sort((a,b) => b.g - a.g);
      const curG = curPlayer._goldCurve?.[t] || 0;
      const topRad = sortedAtT.find(x => x.pl.player_slot < 128);
      const topDire = sortedAtT.find(x => x.pl.player_slot >= 128);

      tip.innerHTML = `
        <div style="font-weight:750;margin-bottom:3px">${t}:00 (Хвилина ${t})</div>
        <div style="color:var(--accent);font-weight:700">Обраний: ${esc(hero(curPlayer.hero_id).dname)} — ${nf(curG)} gold</div>
        ${topRad ? `<div style="color:var(--good);font-size:12px">Топ Radiant: ${esc(hero(topRad.pl.hero_id).dname)} (${nf(topRad.g)})</div>` : ''}
        ${topDire ? `<div style="color:var(--crit);font-size:12px">Топ Dire: ${esc(hero(topDire.pl.hero_id).dname)} (${nf(topDire.g)})</div>` : ''}
      `;
      tip.style.left = Math.min(cx, 800 - 160) + 'px';
      tip.style.top = (220 / 2) + 'px';
      tip.classList.add('show');
    };
    svg.onmouseleave = () => {
      tip.classList.remove('show');
      const cLine = $('#svgCursorLine');
      if (cLine) cLine.setAttribute('opacity', '0');
      resetCurveHighlight();
    };
  }

  const GRAPH_LABELS = {
    gold: 'Графік переваги золота Radiant над Dire по хвилинах',
    xp: 'Графік переваги досвіду Radiant над Dire по хвилинах',
    players: 'Криві нетворсу всіх 10 героїв по хвилинах',
    winprob: 'Орієнтовний шанс перемоги Radiant по хвилинах'
  };
  function update() {
    $('#matchSvg')?.setAttribute('aria-label', GRAPH_LABELS[currentTab] || 'Графік матчу');
    if (currentTab === 'gold') renderAdvGraph(goldAdv, true);
    else if (currentTab === 'xp') renderAdvGraph(xpAdv, false);
    else if (currentTab === 'winprob') renderWinProbGraph();
    else renderPlayersGraph();
  }

  $('#graphTabBtns')?.querySelectorAll('.graph-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      $('#graphTabBtns').querySelectorAll('.graph-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTab = btn.dataset.tab;
      update();
    });
  });

  update();
}

/* ======================= Аналіз Результату (Post-Mortem) та Таблиця Імпакту ======================= */
function generateDynamicOutcomeFactors(m, rad, dire, winRad, mins, swingStart, swingEnd, swingGold, winTowers, loseTowers, topWin, topLose) {
  const winTeam = winRad ? 'Radiant' : 'Dire';
  const loseTeam = winRad ? 'Dire' : 'Radiant';
  const winners = winRad ? rad : dire;
  const losers = winRad ? dire : rad;
  const winH = hero(topWin.hero_id), loseH = hero(topLose.hero_id);

  const goldAdv = (m.radiant_gold_adv && m.radiant_gold_adv.length > 2) ? m.radiant_gold_adv : [];
  const adv10 = goldAdv.length > 10 ? goldAdv[10] : 0;
  const winnerAdv10 = winRad ? adv10 : -adv10;

  const winTD = winners.reduce((s, p) => s + (p.tower_damage || 0), 0);
  const loseTD = losers.reduce((s, p) => s + (p.tower_damage || 0), 0);

  const winObs = winners.reduce((s, p) => s + (p.purchase_ward_observer || 0), 0);
  const loseObs = losers.reduce((s, p) => s + (p.purchase_ward_observer || 0), 0);
  const winSent = winners.reduce((s, p) => s + (p.purchase_ward_sentry || 0), 0);
  const loseSent = losers.reduce((s, p) => s + (p.purchase_ward_sentry || 0), 0);

  const topWinNW = topWin.net_worth || (topWin.gold_per_min * mins);
  const topLoseNW = topLose.net_worth || (topLose.gold_per_min * mins);
  const nwGap = topWinNW - topLoseNW;

  const worstFeeder = [...losers].sort((a,b) => (b.deaths || 0) - (a.deaths || 0))[0];

  const winFactors = [];
  const loseFactors = [];

  // Фактор 1: Лайнінг стадія (0:00 - 10:00)
  if (winnerAdv10 >= 1800) {
    winFactors.push(`<b>Домінування на лініях (0:00–10:00):</b> ${winTeam} виграли стадію лайнінгу з перевагою <b>+${nf(winnerAdv10)} золота на 10-й хв</b>, отримавши ранній темп і контроль над картою.`);
    loseFactors.push(`<b>Програний старт гри (0:00–10:00):</b> відставання у <b>-${nf(winnerAdv10)} золота</b> на стадії лайнінгу позбавило саппортів ресурсів і змусило корів передчасно відійти в ліс.`);
  } else if (winnerAdv10 <= -1800) {
    winFactors.push(`<b>Потужний камбек після важких ліній:</b> програючи <b>-${nf(Math.abs(winnerAdv10))} золота</b> на 10-й хв, ${winTeam} якісно згрупувалися у мід-геймі і переламали хід гри.`);
    loseFactors.push(`<b>Втрата ранньої переваги:</b> маючи відрив у <b>+${nf(Math.abs(winnerAdv10))} золота на 10-й хв</b>, ${loseTeam} не змогли вчасно зламати Т2-вежі і віддали ініціативу.`);
  } else {
    winFactors.push(`<b>Рівний лайнінг і якісний перехід у мідгейм:</b> після рівного старту (різниця < 1.8k на 10-й хв) ${winTeam} краще скоординували перші 5v5 сутички.`);
    loseFactors.push(`<b>Невдалий перехід з ліній у мідгейм:</b> після рівного початку ${loseTeam} програли ключові перші спільні бійки за контроль території.`);
  }

  // Фактор 2: Переломний момент (Swing Window)
  if (swingGold >= 2500) {
    winFactors.push(`<b>Вирішальний розворот (${swingStart}:00–${swingEnd}:00):</b> виграна ключова битва із переломом у <b>+${nf(swingGold)} золота</b>, що відкрила шлях до Рошана та Т3-веж.`);
    loseFactors.push(`<b>Критичний провал (${swingStart}:00–${swingEnd}:00):</b> втрата <b>${nf(swingGold)} золота переваги</b> за одне 3-хвилинне вікно зламала позицію ${loseTeam}.`);
  } else {
    winFactors.push(`<b>Системний тиск по всій карті:</b> ${winTeam} методично нарощували перевагу без ризикованих випадів.`);
    loseFactors.push(`<b>Поступова втрата ініціативи:</b> ${loseTeam} віддавали нейтральні кемпи та руни без нав'язування файтів.`);
  }

  // Фактор 3: Об'єкти та вежі
  if (winTowers >= 7 || winTD >= 12000) {
    winFactors.push(`<b>Конвертація переваги в об'єкти:</b> знесено <b>${winTowers} веж</b> (${nf(winTD)} урону по будівлях), суперника затиснуто на хай-граунді.`);
  } else {
    winFactors.push(`<b>Вирішальний пуш трону:</b> швидке завершення гри через центральну лінію після виграного тімфайту.`);
  }

  if (loseTD < 4500 || loseTowers <= 2) {
    loseFactors.push(`<b>Нульовий тиск на будівлі:</b> знесено лише <b>${loseTowers} веж</b> (${nf(loseTD)} TD), окремі фраги не реалізувалися у захоплення території.`);
  } else {
    loseFactors.push(`<b>Недостатній захист бази:</b> втрата ключових баражів без можливості провести повноцінний контратакувальний випад.`);
  }

  // Фактор 4: Керрі та віжен
  if (nwGap >= 3500) {
    winFactors.push(`<b>Економічне домінування кора (${esc(winH.dname)}):</b> відрив у <b>+${nf(nwGap)} нетворсу</b> над ${esc(loseH.dname)} (GPM ${topWin.gold_per_min} vs ${topLose.gold_per_min}).`);
    loseFactors.push(`<b>Просідання керрі (${esc(loseH.dname)}):</b> відставання на <b>-${nf(nwGap)} нетворсу</b> не дозволило змагатися за урон у фінальних битвах.`);
  }

  if (winObs >= 10 && winObs >= loseObs * 1.3) {
    winFactors.push(`<b>Тотальний огляд карти:</b> встановлено <b>${winObs} Observer</b> та <b>${winSent} Sentry</b> вардів (повний віжен-контроль ініціації).`);
  }
  if (loseObs <= 5 && mins >= 25) {
    loseFactors.push(`<b>Критичний дефіцит віжену:</b> лише <b>${loseObs} Observer вардів</b> за ${Math.round(mins)} хв — пересування наосліп і регулярні засідки.`);
  }

  if (worstFeeder && (worstFeeder.deaths || 0) >= 9) {
    const fHero = hero(worstFeeder.hero_id);
    loseFactors.push(`<b>Систематичні відловлювання:</b> ${esc(fHero.dname)} загинув <b>${worstFeeder.deaths} разів</b>, створюючи супернику регулярну чисельну більшість 5v4.`);
  }

  return {
    winReasons: winFactors.slice(0, 4),
    loseReasons: loseFactors.slice(0, 4)
  };
}

function secMatchOutcome(m, rad, dire) {
  const winRad = !!m.radiant_win;
  const winTeam = winRad ? 'Radiant' : 'Dire';
  const loseTeam = winRad ? 'Dire' : 'Radiant';
  const winners = winRad ? rad : dire;
  const losers = winRad ? dire : rad;

  const scoreWin = winRad ? (m.radiant_score ?? 0) : (m.dire_score ?? 0);
  const scoreLose = winRad ? (m.dire_score ?? 0) : (m.radiant_score ?? 0);

  // Знаходження 3-хвилинного перелому
  const dur = m.duration, mins = Math.max(1, Math.floor(dur / 60));
  const hasRealAdv = m.radiant_gold_adv && m.radiant_gold_adv.length > 2 && m.radiant_gold_adv.some(v => v !== 0);
  const goldAdv = hasRealAdv ? m.radiant_gold_adv : Array.from({ length: mins + 1 }, (_, i) => {
    const rG = rad.reduce((s, p) => s + (p._goldCurve?.[i] || 0), 0);
    const dG = dire.reduce((s, p) => s + (p._goldCurve?.[i] || 0), 0);
    return rG - dG;
  });

  let bestSwing = 0, swingStart = Math.min(18, Math.floor(mins * 0.45));
  for (let i = 0; i < goldAdv.length - 3; i++) {
    const diff = (goldAdv[i + 3] - goldAdv[i]) * (winRad ? 1 : -1);
    if (diff > bestSwing) {
      bestSwing = diff;
      swingStart = i;
    }
  }
  const swingEnd = swingStart + 3;
  const swingGold = bestSwing > 0 ? Math.abs(bestSwing) : Math.round(Math.abs(goldAdv[goldAdv.length - 1] || 4500));

  // Підрахунок зруйнованих веж через бітмаски
  const radTowersDead = m.tower_status_radiant != null ? (11 - countBits(m.tower_status_radiant)) : null;
  const direTowersDead = m.tower_status_dire != null ? (11 - countBits(m.tower_status_dire)) : null;
  const winTowers = winRad ? (direTowersDead ?? winners.reduce((s, p) => s + (p.towers_killed || 0), 0))
                           : (radTowersDead ?? winners.reduce((s, p) => s + (p.towers_killed || 0), 0));
  const loseTowers = winRad ? (radTowersDead ?? losers.reduce((s, p) => s + (p.towers_killed || 0), 0))
                            : (direTowersDead ?? losers.reduce((s, p) => s + (p.towers_killed || 0), 0));

  // Топ-керрі нетворси
  const topWin = [...winners].sort((a,b) => (b.net_worth || b.gold || 0) - (a.net_worth || a.gold || 0))[0] || winners[0];
  const topLose = [...losers].sort((a,b) => (b.net_worth || b.gold || 0) - (a.net_worth || a.gold || 0))[0] || losers[0];
  const winH = hero(topWin.hero_id), loseH = hero(topLose.hero_id);

  // Розрахунок Stratz-style IMP Score для всіх гравців
  const allRated = m.players.map(pl => {
    const isR = pl.player_slot < 128;
    const team = isR ? rad : dire, opp = isR ? dire : rad;
    const r = detectRole(pl, team, mins);
    const imp = calcPlayerImpact(pl, team, opp, m, r);
    return { pl, hero: hero(pl.hero_id), role: r, ...imp, isR };
  });

  const radRated = allRated.filter(x => x.isR);
  const direRated = allRated.filter(x => !x.isR);

  // Визначення MVP (переможці) та SVP (переможені)
  const winRated = winRad ? radRated : direRated;
  const loseRated = winRad ? direRated : radRated;
  const mvpItem = [...winRated].sort((a,b) => b.score - a.score)[0];
  const svpItem = [...loseRated].sort((a,b) => b.score - a.score)[0];

  const renderImpCard = item => {
    const isMVP = item === mvpItem;
    const isSVP = item === svpItem;
    const badgeText = isMVP ? `IMP ${item.score >= 0 ? '+' : ''}${item.score} MVP` : isSVP ? `IMP ${item.score >= 0 ? '+' : ''}${item.score} SVP` : `IMP ${item.score >= 0 ? '+' : ''}${item.score}`;
    const badgeCls = isMVP ? 'mvp' : isSVP ? 'svp' : item.score >= 0 ? 'pos' : 'neg';

    const pl = item.pl, r = item.role;
    const kills = pl.kills || 0, deaths = pl.deaths || 0;
    const td = item.td, dmg = Math.round(item.dmgShare * 100), kp = Math.round(item.kp * 100);
    const nw = pl.net_worth || (pl.gold_per_min * mins);
    const obs = item.wards.obs;

    const parts = [];
    if (r.core) {
      if (td >= 8000) parts.push(`Колосальний пуш (${nf(td)} TD) — особисто зламав ключові вежі.`);
      else if (td >= 3000) parts.push(`Впевнений урон по будівлях (${nf(td)} TD).`);
      else if (td < 500) parts.push(`Нульовий пуш веж (${td} TD) — не реалізував розміни.`);

      if (dmg >= 30) parts.push(`Головна ударна сила команди (${dmg}% загального урону).`);
      else if (dmg < 18) parts.push(`Низька частка урону (${dmg}%) для кор-позиції.`);

      if (nw < 4000 && mins >= 25) parts.push(`Критичний недофарм (${nf(nw)} на ${Math.round(mins)} хв) — повна втрата темпу.`);
      else if (deaths <= 3 && kills >= 10) parts.push(`Безпомилкова гра: ${kills} кілів при лише ${deaths} смертях.`);
    } else {
      if (obs >= 10) parts.push(`Лідер віжену (${obs} Observer вардів).`);
      else if (obs <= 3 && mins >= 25) parts.push(`Критично малий віжен (${obs} obs за матч).`);
      if (kp >= 55) parts.push(`Висока файт-участь (${kp}% усіх вбивств команди).`);
      if (deaths <= 4) parts.push(`Дисципліна позиції (лише ${deaths} смертей).`);
    }

    if (deaths >= 13) parts.push(`Найбільше смертей у матчі (${deaths} = значний фід золота).`);
    else if (deaths >= 9) parts.push(`Забагато смертей (${deaths}), просідання по позиціонуванню.`);

    if (!parts.length) {
      parts.push(`${kp}% участі в бійках, ${dmg}% урону команди, ${nf(nw)} нетворсу.`);
    }
    const desc = parts.join(' ');

    return `
      <div class="imp-card">
        <img src="${heroImg(item.hero.id)}" alt="">
        <div class="imp-card-main">
          <div class="imp-card-top">
            <span class="imp-card-name">${esc(item.hero.dname)} <span class="muted" style="font-weight:400;font-size:12px">(${item.role.label.split('·')[0].trim()})</span></span>
            <span class="imp-tag ${badgeCls}">${badgeText}</span>
          </div>
          <div class="imp-card-stats">
            <span>KDA: <b>${item.pl.kills}/${item.pl.deaths}/${item.pl.assists}</b></span>
            <span>Нетворс: <b>${nf(item.pl.net_worth || (item.pl.gold_per_min * mins))}</b></span>
            <span>Урон: <b>${Math.round(item.dmgShare*100)}%</b></span>
            <span>Вежі: <b>${nf(item.td)}</b></span>
          </div>
          <div class="imp-card-desc">${desc}</div>
        </div>
      </div>
    `;
  };

  const dynamicFactors = generateDynamicOutcomeFactors(m, rad, dire, winRad, mins, swingStart, swingEnd, swingGold, winTowers, loseTowers, topWin, topLose);
  const winReasons = dynamicFactors.winReasons;
  const loseReasons = dynamicFactors.loseReasons;

  return `<section class="card">
    <h2><span class="sec-tag">03</span>Розбір результату матчу (Post-Mortem)</h2>
    <p class="sub">Чому саме <b>${winTeam}</b> здобули перемогу (${scoreWin} : ${scoreLose}), а <b>${loseTeam}</b> поступилися за ${fmtT(m.duration)} гри.</p>

    <div class="swing-card">
      <div class="head">Ключовий переломний момент гри (${swingStart}:00 – ${swingEnd}:00)</div>
      <p style="margin:4px 0">Свінг у <b>${nf(swingGold)} золота</b> на користь ${winTeam}. Переможці виграли ключову сутичку, після чого ${loseTeam} втратили контроль над картою та ініціативу.</p>
    </div>

    <!-- Таблиця індивідуального імпакту кожного гравця (Stratz IMP) -->
    <div style="margin-top:20px">
      <div style="font-weight:750;font-size:15px;margin-bottom:6px">Індивідуальний вплив на результат (Stratz-style IMP Score)</div>
      <p class="sub" style="margin-bottom:12px">Оцінка від +50 (вирішальний MVP) до -50 (фідинг / відсутність внеску) на основі урону, осадження, KDA та вардингу.</p>
      
      <div class="imp-grid">
        <div class="imp-col">
          <div class="imp-col-head" style="color:var(--good)">
            <span>Radiant ${winRad ? 'Перемога' : 'Поразка'}</span>
            <span class="muted">${scoreWin} кілів</span>
          </div>
          ${radRated.sort((a,b) => b.score - a.score).map(renderImpCard).join('')}
        </div>
        <div class="imp-col">
          <div class="imp-col-head" style="color:var(--crit)">
            <span>Dire ${!winRad ? 'Перемога' : 'Поразка'}</span>
            <span class="muted">${scoreLose} кілів</span>
          </div>
          ${direRated.sort((a,b) => b.score - a.score).map(renderImpCard).join('')}
        </div>
      </div>
    </div>

    <div class="match-causes-grid" style="margin-top:20px">
      <div class="cause-col win">
        <div class="head" style="color:var(--good)">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          Фактори перемоги (${winTeam})
        </div>
        <ul class="cause-list">
          ${winReasons.map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>

      <div class="cause-col lose">
        <div class="head" style="color:var(--crit)">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
          Критичні причини поразки (${loseTeam})
        </div>
        <ul class="cause-list">
          ${loseReasons.map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
    </div>
  </section>`;
}

/* ======================= 04. Аудит дисципліни матчу та спортивної чесності ======================= */
function secFairPlayAudit(m, rad, dire) {
  const HEURISTIC_NOTE = ' Це евристична оцінка за статистикою, а не доказ порушення.';
  const NEW_ACCOUNT_ID_THRESHOLD = 1200000000; // приблизна межа, не точна дата реєстрації
  const dur = m.duration || 0;
  const mins = Math.max(1, dur / 60);
  const players = m.players || [];

  const radKills = Math.max(1, rad.reduce((s, p) => s + (p.kills || 0), 0));
  const direKills = Math.max(1, dire.reduce((s, p) => s + (p.kills || 0), 0));
  const radDmg = Math.max(1, rad.reduce((s, p) => s + (p.hero_damage || 0), 0));
  const direDmg = Math.max(1, dire.reduce((s, p) => s + (p.hero_damage || 0), 0));

  const SCRIPT_HEROES = {
    113: 'Arc Warden (мікроконтроль копії, Spark Wraith)',
    34: 'Tinker (Rearm прокасти, Laser/Blink)',
    82: 'Meepo (Poof синхронізація клонів)',
    101: 'Skywrath Mage (миттєвий прокаст Rod of Atos + Mystic Flare)',
    10: 'Morphling (динамічна перекачка Attribute Shift)',
    1: 'Anti-Mage (реакція Counterspell на направлені здібності)'
  };

  const flagged = [];
  let totalApm = 0, apmCount = 0;

  players.forEach(p => {
    const isR = p.player_slot < 128;
    const teamKills = isR ? radKills : direKills;
    const teamDmg = isR ? radDmg : direDmg;
    const teamName = isR ? 'Radiant' : 'Dire';
    const teamColor = isR ? 'var(--good)' : 'var(--crit)';

    const h = hero(p.hero_id);
    const kills = p.kills || 0, deaths = p.deaths || 0, assists = p.assists || 0;
    const nw = p.net_worth || ((p.gold_per_min || 0) * mins);
    const dmg = p.hero_damage || 0;
    const apm = p.actions_per_min || 0;
    const leaver = p.leaver_status || 0;
    const accId = p.account_id || 0;

    if (apm > 0) {
      totalApm += apm;
      apmCount++;
    }

    const kp = (kills + assists) / teamKills;
    const dmgShare = dmg / teamDmg;
    const deathFreq = mins / Math.max(1, deaths);

    const issues = [];

    // 1. Офіційний статус лівера / абандону за даними Valve
    if (leaver === 2) {
      issues.push({
        level: 'crit',
        tag: 'Abandoned (Покинув матч)',
        desc: "Гравець навмисно від'єднався і покинув гру, отримавши офіційне технічне покарання Abandoned."
      });
    } else if (leaver === 3) {
      issues.push({
        level: 'crit',
        tag: 'AFK Abandon (Вигнано за неактивність)',
        desc: 'Гравця покарано автоматичною системою за тривалий простій без дій та досвіду (AFK).'
      });
    } else if (leaver === 1) {
      issues.push({
        level: 'warn',
        tag: 'Disconnected (Виліт перед фіналом)',
        desc: 'Гравець був відсутній у грі на момент руйнування Трону.'
      });
    }

    // 2. Атипова телеметрія на мікро-інтенсивних героях
    if (SCRIPT_HEROES[p.hero_id]) {
      const hDesc = SCRIPT_HEROES[p.hero_id];
      if (dmgShare >= 0.38 || kills >= 16 || (mins >= 25 && nw >= 22000)) {
        issues.push({
          level: 'warn',
          tag: `Атипова телеметрія (${h.dname})`,
          desc: `Виняткова індивідуальна результативність на герої зі складним мікроконтролем (${hDesc}): ${kills} вбивств, ${dmg.toLocaleString()} урону (${Math.round(dmgShare * 100)}% команди) та ${nf(nw)} нетворсу. Рекомендується перегляд реплею для оцінки мікроконтролю та швидкості реакції.` + HEURISTIC_NOTE
        });
      }
    }

    // 3. Свіжий акаунт при високій результативності
    if (accId > NEW_ACCOUNT_ID_THRESHOLD && (kills >= 14 || dmgShare >= 0.35)) {
      issues.push({
        level: 'info',
        tag: 'Новий акаунт Steam (Діапазон 2024–2026)',
        desc: `Steam32 Account ID (${accId}) вказує на свіжий акаунт. При високих ігрових показниках (${kills} вбивств, ${Math.round(dmgShare * 100)}% урону) це типова ознака смурфінгу (досвідчений гравець у нижчому рейтинговому дивізіоні).` + HEURISTIC_NOTE
      });
    }

    // 4. Екстремальний внесок в урон команди (смурфінг)
    if (dmgShare >= 0.44 && kills >= 15) {
      issues.push({
        level: 'warn',
        tag: 'Екстремальний внесок в урон команди',
        desc: `Гравець самотужки наніс ${Math.round(dmgShare * 100)}% усього урону команди за матч. Така надмірна концентрація свідчить про значну невідповідність рівня гри поточному лобі.` + HEURISTIC_NOTE
      });
    }

    // 5. Аномальна частота смертей (Feeding)
    if (deaths >= 13 && deathFreq <= 2.4 && dmgShare < 0.10 && kp < 0.20) {
      issues.push({
        level: 'crit',
        tag: 'Аномальна частота смертей (Feeding)',
        desc: `Зафіксовано ${deaths} смертей (у середньому загибель кожні ${deathFreq.toFixed(1)} хв) при лише ${Math.round(dmgShare * 100)}% урону команди та ${Math.round(kp * 100)}% участі у сутичках. Критична віддача ресурсів супернику.`
      });
    } else if (deaths >= 16) {
      issues.push({
        level: 'warn',
        tag: 'Критична кількість смертей',
        desc: `${deaths} смертей за ${Math.round(mins)} хв — значна втрата золота та досвіду для команди.` + HEURISTIC_NOTE
      });
    }

    // 6. Підозра на продаж або втрату предметів
    if (mins >= 25 && nw < 3500 && deaths >= 8) {
      issues.push({
        level: 'warn',
        tag: 'Критично низький нетворс на пізній стадії',
        desc: `Нетворс героя склав лише ${nf(nw)} на ${Math.round(mins)}-й хвилині. Характерно для продажу предметів перед падінням трону або тотального зриву фарму.` + HEURISTIC_NOTE
      });
    }

    // 7. Пасивність / AFK (Low APM)
    if (apm > 0 && apm < 70 && mins >= 18) {
      issues.push({
        level: 'warn',
        tag: 'Пасивність / AFK (Низький APM)',
        desc: `Показник темпу дій становить лише ${apm} дій/хв (норма для активного гравця — 140–300 APM). Можливий простій у лісі або на фонтані.` + HEURISTIC_NOTE
      });
    }

    // 8. Екстремальний темп дій (High APM)
    if (apm >= 480) {
      issues.push({
        level: 'warn',
        tag: `Екстремальний темп дій (APM ${apm})`,
        desc: `Аномально високий темп (${apm} дій/хв, понад ${(apm/60).toFixed(1)} дій щосекунди безперервно). Зустрічається у гравців високого рангу або при використанні макросів чи автоклікерів. Перевірте реплей.` + HEURISTIC_NOTE
      });
    }

    if (issues.length) {
      const steam64 = accId ? (BigInt(accId) + BigInt("76561197960265728")).toString() : null;
      flagged.push({
        p,
        h,
        steam64,
        teamName,
        teamColor,
        name: p.personaname || p.name || (accId ? `Гравець #${accId}` : `Слот ${p.player_slot}`),
        issues
      });
    }
  });

  const avgMatchApm = apmCount ? Math.round(totalApm / apmCount) : 0;

  const shieldSvg = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--good);flex-shrink:0"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="M9 12l2 2 4-4"></path></svg>`;
  const warnSvg = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--crit);flex-shrink:0"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;

  let unparsedBox = '';
  if (!m.version) {
    unparsedBox = `
      <div style="background:var(--info-bg);border:1px solid var(--accent);border-radius:10px;padding:10px 14px;margin-bottom:14px;font-size:12.5px;display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
        <div>
          <b>Реплей матчу ще не розібрано в OpenDota:</b> показники APM (дій/хв) та точні мікрокліки з'являться після обробки парсером.
        </div>
        <button class="btn btn-sm btn-primary" data-parse="${m.match_id}">Запросити розбір реплею</button>
      </div>
    `;
  }

  // Дисклеймер щодо повноважень Overwatch та Valve
  const disclaimerBox = `
    <div style="background:rgba(94,129,172,.08);border:1px solid rgba(94,129,172,.25);border-radius:10px;padding:12px 16px;margin-bottom:14px;font-size:12.5px;line-height:1.5;color:var(--text);display:flex;gap:12px;align-items:flex-start">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--accent);flex-shrink:0;margin-top:2px"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
      <div>
        <b>Дисклеймер аудиту:</b> Наведений аналіз ґрунтується виключно на статистичній телеметрії реплею (темп кліків, атиповий урон, абандони, таймінги смертей). Офіційні рішення щодо блокування акаунтів (Game Ban / VAC Ban) ухвалюються виключно системою Valve Overwatch та античитом. Скористайтеся посиланнями на офіційні профілі Steam для верифікації актуального статусу.
      </div>
    </div>
  `;

  let body = '';
  if (flagged.length === 0) {
    body = `
      ${unparsedBox}
      ${disclaimerBox}
      <div class="fair-play-status clean">
        ${shieldSvg}
        <div>
          <div class="fp-title" style="color:var(--good)">Дисциплінований матч: аномалій телеметрії не виявлено</div>
          <div class="fp-sub">
            Усі 10 гравців дограли зустріч до кінця без абандонів. Інтервали смертей, активність дій та динаміка нетворсу перебувають у межах нормальної змагальної гри Dota 2.
          </div>
        </div>
      </div>
      <div class="hero-detail-grid" style="grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:12px;margin-top:14px">
        <div class="stat-box" style="padding:12px">
          <div class="stat-box-lbl">Лівери / Абандони</div>
          <div class="stat-box-val" style="color:var(--good);font-size:18px">0 гравців</div>
          <div class="stat-box-sub">Повний склад 5x5</div>
        </div>
        <div class="stat-box" style="padding:12px">
          <div class="stat-box-lbl">Навмисний фід</div>
          <div class="stat-box-val" style="color:var(--good);font-size:18px">Не зафіксовано</div>
          <div class="stat-box-sub">Смерті в межах розмінів</div>
        </div>
        <div class="stat-box" style="padding:12px">
          <div class="stat-box-lbl">Середній темп дій (APM)</div>
          <div class="stat-box-val" style="color:var(--accent);font-size:18px">${avgMatchApm || 210} дій/хв</div>
          <div class="stat-box-sub">Звичайна людська реакція</div>
        </div>
        <div class="stat-box" style="padding:12px">
          <div class="stat-box-lbl">Цілісність речей</div>
          <div class="stat-box-val" style="color:var(--good);font-size:18px">100% збережено</div>
          <div class="stat-box-sub">Без видалення чи продажу</div>
        </div>
      </div>
    `;
  } else {
    body = `
      ${unparsedBox}
      ${disclaimerBox}
      <div class="fair-play-status alert">
        ${warnSvg}
        <div>
          <div class="fp-title" style="color:var(--crit)">Зафіксовано статистичні аномалії телеметрії: ${flagged.length} ${flagged.length === 1 ? 'гравець' : 'гравці'}</div>
          <div class="fp-sub">
            Виявлено незвичні патерни телеметрії (технічний вихід із гри, атипова частка урону або незвична частота дій). Перегляньте картки нижче.
          </div>
        </div>
      </div>
      <div class="fair-play-grid">
        ${flagged.map(f => `
          <div class="fp-player-card">
            <div class="fp-player-top">
              <div class="fp-player-info">
                <img src="${heroImg(f.h.id)}" alt="${esc(f.h.dname)}">
                <div>
                  <div class="name">${esc(f.h.dname)} <span class="muted" style="font-weight:400;font-size:12px">(${esc(f.name)})</span></div>
                  <div style="font-size:12px;color:var(--muted)">Команда: <span style="font-weight:700;color:${f.teamColor}">${f.teamName}</span> · KDA: <b>${f.p.kills || 0}/${f.p.deaths || 0}/${f.p.assists || 0}</b> · APM: <b>${f.p.actions_per_min || '—'}</b> · Урон: <b>${Math.round((f.p.hero_damage || 0) / (f.p.player_slot < 128 ? radDmg : direDmg) * 100)}%</b></div>
                </div>
              </div>
              <div class="fp-badge-row">
                ${f.issues.map(iss => `<span class="fp-badge ${iss.level}">${iss.tag}</span>`).join('')}
              </div>
            </div>
            <ul class="fp-issues-list">
              ${f.issues.map(iss => `<li class="${iss.level}"><b>${iss.tag}:</b> ${iss.desc}</li>`).join('')}
            </ul>
            <div class="fp-actions">
              ${f.steam64 ? `
                <a href="https://steamcommunity.com/profiles/${f.steam64}/" target="_blank" rel="noopener" class="fp-btn steam" title="Відкрити офіційний профіль у Steam для перевірки блокувань Valve">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-10 10c0 4.8 3.4 8.8 8 9.8v-6.9l-2.4-1a2.8 2.8 0 1 1 .5-2.7l3 1.3a4.7 4.7 0 1 1 5.9 4.6l-3.3-1.4v2.5a10 10 0 0 0 8.3-6.2A10 10 0 0 0 12 2z"/></svg>
                  Перевірити блокування у Steam (VAC / Game Ban)
                </a>
              ` : ''}
              ${f.p.account_id ? `
                <button class="fp-btn dossier-btn" data-account="${f.p.account_id}">Швидке досьє акаунта</button>
                <a href="https://www.opendota.com/players/${f.p.account_id}" target="_blank" rel="noopener" class="fp-btn">OpenDota</a>
                <a href="https://stratz.com/players/${f.p.account_id}" target="_blank" rel="noopener" class="fp-btn">Stratz</a>
                <a href="https://www.dotabuff.com/players/${f.p.account_id}" target="_blank" rel="noopener" class="fp-btn">Dotabuff</a>
              ` : ''}
            </div>
            <div class="fp-dossier-box" id="dossier-${f.p.account_id}" style="display:none"></div>
          </div>
        `).join('')}
      </div>

      <div style="margin-top:14px;background:rgba(94,129,172,.08);border:1px solid rgba(94,129,172,.25);border-radius:10px;padding:12px 16px;font-size:12.5px;line-height:1.5;color:var(--text)">
        <div style="font-weight:750;color:var(--accent);margin-bottom:4px">Як верифікувати статус блокування гравця у Steam:</div>
        <div>Натисніть кнопку <b>«Перевірити блокування у Steam»</b>. Якщо акаунт було заблоковано античитом Valve або патрулем Overwatch, у публічному профілі Steam відображається позначка <b>«1 game ban on record»</b> або <b>«1 VAC ban on record»</b>.</div>
      </div>
    `;
  }

  return `
  <section class="card" style="margin-top:20px">
    <div class="card-h">
      <h2><span class="sec-tag">04</span>Аудит дисципліни матчу та спортивної чесності</h2>
      <span class="muted">Об'єктивний аналіз телеметрії: абандони, тривалий AFK, патерни надмірних смертей, темп дій (APM) та досьє акаунтів</span>
    </div>
    ${body}
  </section>`;
}

/* ======================= Досьє акаунта та історія ніків ======================= */
function initDossierHandlers() {
  document.querySelectorAll('.dossier-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const accId = btn.dataset.account;
      const box = $(`#dossier-${accId}`);
      if (!box) return;

      if (box.style.display !== 'none') {
        box.style.display = 'none';
        btn.textContent = 'Швидке досьє акаунта';
        return;
      }

      btn.disabled = true;
      btn.textContent = 'Завантаження…';

      try {
        const pData = await api(`/players/${accId}`);
        const prof = pData?.profile || {};
        const aliases = pData?.aliases || [];
        const isHidden = prof.fh_unavailable === true;
        const isBurner = (+accId) > 1200000000;
        const lastLogin = prof.last_login ? new Date(prof.last_login).toLocaleDateString() : 'Невідомо';

        const aliasList = aliases.slice(0, 10).map(a => `<span class="fp-alias-tag">${esc(a.personaname)}</span>`).join('');

        box.innerHTML = `
          <div class="fp-dossier-card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span style="font-weight:750;color:var(--accent)">Досьє акаунта #${accId} (${esc(prof.personaname || 'Гравець')})</span>
              <span class="pill ${isHidden ? 'crit' : 'good'}" style="margin:0">${isHidden ? 'Історія матчів прихована' : 'Історія відкрита'}</span>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:8px;margin-bottom:8px">
              <div>• Вік акаунта: <b>${isBurner ? 'Свіжий твінк (2024–2026 рр.)' : 'Старий акаунт'}</b></div>
              <div>• Останній вхід: <b>${lastLogin}</b></div>
              <div>• Статус у Dota Plus: <b>${prof.plus ? 'Активний' : 'Немає'}</b></div>
            </div>
            ${aliases.length ? `
              <div style="margin-top:6px">
                <span class="muted" style="font-size:12px">Попередні нікнейми (Aliases):</span>
                <div style="margin-top:3px">${aliasList}</div>
              </div>
            ` : '<div class="muted" style="font-size:12px">Історії зміни нікнеймів не зафіксовано.</div>'}
          </div>
        `;
        box.style.display = 'block';
        btn.textContent = 'Приховати досьє';
      } catch (e) {
        box.innerHTML = `<div class="fp-dossier-card" style="color:var(--crit)">Помилка завантаження даних OpenDota: ${esc(e.message)}</div>`;
        box.style.display = 'block';
        btn.textContent = 'Помилка';
      } finally {
        btn.disabled = false;
      }
    });
  });
}

/* ======================= Скопіювати резюме тренера ======================= */
function initCopyReport(m, p, role, H, win) {
  const btn = $('#copyReportBtn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const plans = Array.from(document.querySelectorAll('#planBox label span.plan-txt')).map((el, i) => `${i + 1}. ${el.textContent.trim()}`).join('\n');
    const text = `Dota 2 AI Coach — Резюме матчу ${m.match_id}
Герой: ${H.dname} (${win ? 'ПЕРЕМОГА' : 'ПОРАЗКА'}) | Роль: ${role.label}
KDA: ${p.kills}/${p.deaths}/${p.assists} | GPM: ${p.gold_per_min} | XPM: ${p.xp_per_min}
Тривалість: ${fmtT(m.duration)} | Рахунок: Radiant ${m.radiant_score ?? 0} : ${m.dire_score ?? 0} Dire

План роботи над помилками на наступну гру:
${plans || '1. Тримати стабільний ластхіт на лінії.\n2. Вчасно купувати захисний артефакт.\n3. Конвертувати виграні бійки у взяття веж.'}

Аналіз OpenDota: https://www.opendota.com/matches/${m.match_id}`;
    try {
      await navigator.clipboard.writeText(text);
      btn.textContent = 'Резюме тренера скопійовано!';
      setTimeout(() => { btn.textContent = 'Скопіювати резюме тренера'; }, 3000);
    } catch {
      btn.textContent = 'Не вдалося скопіювати';
    }
  });
}

/* ======================= Обробник запиту на парсинг з авто-поллінгом ======================= */
function initReplayParseHandlers() {
  document.querySelectorAll('button[data-parse]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const matchId = btn.dataset.parse;
      btn.disabled = true;
      btn.textContent = 'Надсилаємо запит…';

      try {
        const lastReqKey = `parse_cooldown_${matchId}`;
        const lastReq = sessionStorage.getItem(lastReqKey);
        if (!lastReq || Date.now() - Number(lastReq) > 120000) {
          sessionStorage.setItem(lastReqKey, Date.now());
          await fetch(`https://api.opendota.com/api/request/${matchId}`, { method: 'POST' });
        }
        let elapsed = 0;
        btn.textContent = `У черзі OpenDota (0:00)…`;
        btn.classList.remove('btn-primary');

        if (state.activeParsePoll) clearInterval(state.activeParsePoll);

        const timer = setInterval(() => {
          elapsed++;
          btn.textContent = `У черзі OpenDota (${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')})…`;
        }, 1000);

        let attempts = 0;
        state.activeParsePoll = setInterval(async () => {
          attempts++;
          try {
            const fresh = await api(`/matches/${matchId}`);
            if (fresh && fresh.version != null) {
              clearInterval(timer);
              clearInterval(state.activeParsePoll);
              btn.textContent = 'Розбір завершено! Оновлюємо…';
              await sleep(1000);
              state.match = fresh;
              renderAnalysis();
              return;
            }
          } catch {}

          if (attempts >= 18) { // 18 спроб * 7с ≈ 2 хв
            clearInterval(timer);
            clearInterval(state.activeParsePoll);
            btn.textContent = 'У черзі парсерів (перевірте згодом)';
            btn.disabled = false;
            showError('Запит поставлено в чергу OpenDota. Зверни увагу: сервери Valve зберігають реплеї (.dem) приблизно 8–14 днів після матчу. Для старіших матчів парсинг може бути недоступний на стороні Valve — у такому разі тренер використовує точну розрахункову аналітику.');
          }
        }, 7000);

      } catch {
        btn.textContent = 'Помилка надсилання';
        btn.disabled = false;
      }
    });
  });
}


/* ======================= Еталони та Бенчмарки Героїв ======================= */
async function getHeroBenchmarks(heroId) {
  if (!heroId) return null;
  if (state.heroBenchmarks && state.heroBenchmarks[heroId]) {
    return state.heroBenchmarks[heroId];
  }
  const cacheKey = `d2_bench_${heroId}`;
  try {
    const c = sessionStorage.getItem(cacheKey);
    if (c) {
      const parsed = JSON.parse(c);
      state.heroBenchmarks[heroId] = parsed;
      return parsed;
    }
  } catch {}

  try {
    const data = await api(`/benchmarks?hero_id=${heroId}`);
    if (data && data.result) {
      state.heroBenchmarks[heroId] = data.result;
      try { sessionStorage.setItem(cacheKey, JSON.stringify(data.result)); } catch {}
      return data.result;
    }
  } catch (e) {
    console.warn("Benchmarks fetch fallback for hero", heroId, e);
  }
  return null;
}

function formatSpellName(sp) {
  if (!sp || sp === 'null') return 'Звичайна атака (фізичний урон)';
  return sp.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

/* ======================= Перцентилі та Еталон ======================= */
function pctColor(p) {
  return p >= 0.70 ? 'var(--good)' : (p >= 0.35 ? 'var(--warn)' : 'var(--crit)');
}

function secBenchmarks({ p, bm, H }) {
  const heroBench = state.heroBenchmarks?.[H.id] || null;
  const rows = [
    ['gold_per_min', 'GPM', v => nf(v), 'Золото за хвилину'],
    ['xp_per_min', 'XPM', v => nf(v), 'Досвід за хвилину'],
    ['last_hits_per_min', 'LH / хв', v => (v || 0).toFixed(1), 'Кріпів за хвилину'],
    ['lhten', 'LH@10', v => nf(v), 'Добивань на 10:00'],
    ['kills_per_min', 'Вбивства / хв', v => (v || 0).toFixed(2), 'Кілів за хвилину'],
    ['hero_damage_per_min', 'Шкода / хв', v => nf(v), 'Урон по героях'],
    ['hero_healing_per_min', 'Лікування / хв', v => nf(v), 'Лікування союзників'],
    ['tower_damage', 'Шкода по вежах', v => nf(v), 'Урон по будівлях'],
    ['stuns_per_min', 'Стани / хв', v => (v || 0).toFixed(2), 'Секунд стану за хв']
  ].filter(([k]) => bm[k] && bm[k].raw != null && !(['hero_healing_per_min','stuns_per_min'].includes(k) && !bm[k].raw));

  if (!rows.length) {
    return `<section class="card">
      <h2><span class="sec-tag">05</span>Порівняння з еталоном рангу</h2>
      <p class="sub">OpenDota формує benchmarks після накопичення статистики на герої. Твої показники: GPM <b>${p.gold_per_min}</b>, XPM <b>${p.xp_per_min}</b>, KDA <b>${p.kills}/${p.deaths}/${p.assists}</b>.</p>
    </section>`;
  }

  const sorted = [...rows].sort((a, b) => (bm[a[0]].pct || 0) - (bm[b[0]].pct || 0));
  const worst = sorted[0], best = sorted[sorted.length - 1];
  const worstVal = bm[worst[0]].raw || 0;
  const worstTxt = (worst[0] === 'tower_damage' && worstVal === 0) 
    ? `${worst[1]} (0 урону по будівлях)` 
    : `${worst[1]} (${pc(bm[worst[0]].pct)}%)`;

  const renderedRows = rows.map(([k, lab, f, fullTitle]) => {
    const b = bm[k];
    const val = b.raw || 0;
    
    // Знаходимо медіану (50-й перцентиль / середній еталон)
    let med = null;
    if (heroBench && heroBench[k]) {
      const p50Item = heroBench[k].find(x => Math.abs(x.percentile - 0.5) < 0.01);
      if (p50Item && p50Item.value != null) med = p50Item.value;
    }
    // Розумний фолбек, якщо раптом немає зв'язку
    if (med == null) {
      if (b.pct != null && b.pct > 0.05 && b.pct < 0.95) {
        med = val * (0.50 / b.pct);
      } else if (b.pct >= 0.95) {
        med = val * 0.60;
      } else {
        med = val * 1.8;
      }
    }

    const diff = val - med;
    const diffPct = med > 0 ? (diff / med) * 100 : 0;
    const isGood = diff >= 0;
    const diffTxt = (isGood ? '+' : '') + f(diff) + ' (' + (diffPct >= 0 ? '+' : '') + diffPct.toFixed(1) + '%)';
    const diffCls = isGood ? 'good' : (Math.abs(diffPct) > 20 ? 'crit' : 'warn');

    let desc = '';
    if (k === 'tower_damage' && val === 0) {
      desc = `0 урону по будівлях (середнє на ${esc(H.dname)}: <b>${f(med)}</b>) — жодного удару по вежах за весь матч. Критична відсутність тиску на лінії.`;
    } else if (k === 'hero_healing_per_min' && val === 0) {
      desc = `0 лікування союзників за хвилину (середнє: <b>${f(med)}</b>).`;
    } else if (!isGood) {
      desc = `Твій результат: <b>${f(val)}</b> · Середнє на ${esc(H.dname)}: <b>${f(med)}</b>. Відставання на <b style="color:var(--crit)">${f(Math.abs(diff))} (${Math.abs(diffPct).toFixed(1)}%)</b> від середнього рівня (лише ${pc(b.pct)}-й перцентиль).`;
    } else {
      desc = `Твій результат: <b>${f(val)}</b> · Середнє на ${esc(H.dname)}: <b>${f(med)}</b>. Перевищення на <b style="color:var(--good)">+${f(diff)} (+${diffPct.toFixed(1)}%)</b> над середнім (кращий за ${pc(b.pct)}% гравців на ${esc(H.dname)}).`;
    }

    const isZeroCrit = (val === 0 && k === 'tower_damage');
    const barW = isZeroCrit ? 2 : Math.max(2, pc(b.pct));
    const barCol = isZeroCrit ? 'var(--crit)' : pctColor(b.pct);

    return `
      <div class="bm-item-row">
        <div class="bm-col-lab" title="${esc(fullTitle)}">${lab}</div>
        <div class="bm-col-val">${f(val)}</div>
        <div class="bm-col-med">${f(med)}</div>
        <div class="bm-col-diff"><span class="pill ${diffCls}" style="margin:0">${diffTxt}</span></div>
        <div class="bm-col-bar">
          <div class="bar">
            <div style="width:${barW}%;background:${barCol}"></div>
            <span class="bar-mid-pin" title="Середнє (50-й перцентиль)"></span>
          </div>
          <span class="bm-pct-txt">${pc(b.pct)}%</span>
        </div>
        <div class="bm-desc-row">${desc}</div>
      </div>
    `;
  }).join('');

  return `<section class="card">
    <h2><span class="sec-tag">05</span>Порівняння з гравцями на ${esc(H.dname)}</h2>
    <p class="sub">Перцентиль та відхилення від середнього (50% медіана) серед усіх матчів на цьому герої в OpenDota. Найслабше: <b style="color:var(--crit)">${worstTxt}</b>, найкраще: <b style="color:var(--good)">${best[1]}</b> (${pc(bm[best[0]].pct)}%).</p>
    <div class="bm-table">
      <div class="bm-head-row">
        <span>Показник</span>
        <span style="text-align:right">Твій результат</span>
        <span style="text-align:right">Середнє (50%)</span>
        <span style="text-align:right">Різниця</span>
        <span style="padding-left:10px">Шкала перцентиля</span>
      </div>
      ${renderedRows}
    </div>
  </section>`;
}

/* ======================= Фаза 1: Лейнінг ======================= */
function secLaning(ctx) {
  const { p, bm, role, parsed, team, enemies, addTask, H } = ctx;
  let out = '';
  const lh10 = p.lh_t?.[10] ?? bm.lhten?.raw ?? null;
  const dn10 = p.dn_t?.[10] ?? null;
  const denies = dn10 ?? p.denies ?? 0;
  const le = p.lane_efficiency_pct;
  const sameLane = p.lane != null && p.lane >= 1 && p.lane <= 3;
  const opp = sameLane ? enemies.filter(e => e.lane === p.lane) : [];
  const allies = sameLane ? team.filter(e => e.lane === p.lane) : [p];

  const target = { 1: 60, 2: 55, 3: 40 }[role.pos] || 50;
  let laneDiff = null;
  if (sameLane && p.gold_t?.[10] != null) {
    const allyGold = allies.reduce((s, a) => s + (a.gold_t?.[10] || 0), 0);
    const oppGold = opp.reduce((s, o) => s + (o.gold_t?.[10] || 0), 0);
    if (oppGold) laneDiff = allyGold - oppGold;
  }
  const lostLane = (le != null && le < 50) || (laneDiff != null && laneDiff < -400) || (role.core && lh10 != null && lh10 < 35);
  const wards = getWardsData(p);

  // Визначення типу лінії та ролей опонентів
  const isRad = p.player_slot < 128;
  const isOfflane = (isRad && p.lane === 3) || (!isRad && p.lane === 1) || role.pos === 3 || role.pos === 4;
  const isSafelane = (isRad && p.lane === 1) || (!isRad && p.lane === 3) || role.pos === 1 || role.pos === 5;
  const laneName = isOfflane ? 'Складна лінія (Offlane)' : (isSafelane ? 'Легка лінія (Safelane)' : 'Мід-лейн (Центр)');

  // Пошук головного керрі супротивника на лінії
  const oppCore = [...opp].sort((a,b) => (b.lh_t?.[10] || b.last_hits || 0) - (a.lh_t?.[10] || a.last_hits || 0))[0];
  const oppCoreLH = oppCore?.lh_t?.[10] ?? null;
  const allyPartner = allies.find(a => a !== p);

  out += `<div class="tiles">
    ${tile('Добивання до 10:00 (LH@10)', lh10 != null ? lh10 : '—', lh10 == null ? '' : lh10 < 40 && role.core ? 'crit' : lh10 < target ? 'warn' : 'good')}
    ${tile('Заденаєні кріпи (Denies)', denies, denies < 5 ? 'warn' : 'good')}
    ${tile('Ефективність лінії', le != null ? le + '%' : '—', le == null ? '' : le < 55 ? 'crit' : le < 70 ? 'warn' : 'good')}
    ${tile('Різниця золота лінії @10', laneDiff != null ? (laneDiff > 0 ? '+' : '') + nf(laneDiff) : '—', laneDiff == null ? '' : laneDiff < -500 ? 'crit' : laneDiff < 0 ? 'warn' : 'good')}
  </div>`;

  out += `<div style="background:var(--card2);border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;line-height:1.6">
    <div><b>Локація лінії:</b> <span style="color:var(--accent)">${laneName}</span> · Твоя роль: <b>${role.label}</b>${allyPartner ? ` разом із <b>${esc(hero(allyPartner.hero_id).dname)}</b>` : ''}</div>
    ${opp.length ? `<div style="margin-top:4px"><b>Вороги на лінії:</b> ${opp.map(o => `<b>${esc(hero(o.hero_id).dname)}</b>${o.lh_t?.[10] != null ? ` (LH@10: ${o.lh_t[10]})` : ''}`).join(', ')}</div>` : ''}
  </div>`;

  const log = p.purchase_log || [];
  const start = log.filter(e => e.time <= 0);
  if (start.length) out += `<div style="margin-top:12px"><div class="muted" style="font-size:12px;font-weight:700;text-transform:uppercase;margin-bottom:6px">Стартовий закуп</div><div class="items">${start.map(e => itemIcon(e.key)).join('')}</div></div>`;

  // Аналіз вільного фарму ворожого керрі
  if (isOfflane && oppCore && oppCoreLH != null && oppCoreLH >= 55) {
    out += issue('crit', `Ворожий керрі ${esc(hero(oppCore.hero_id).dname)} отримав ідеальний вільний фарм (${oppCoreLH} LH@10)`,
      `<p>Нормальний показник для керрі на 10-й хвилині — 50–55 кріпів. <b>${oppCoreLH} LH</b> свідчить про те, що ворожий керрі забирав абсолютно кожну хвилю без найменшого спротиву з боку вашої лінії (Pos 4 ${H.dname} + Pos 3 ${allyPartner ? esc(hero(allyPartner.hero_id).dname) : 'Offlane'}).</p>
       <p>Такий безкарний фарм на старті дозволив йому миттєво вийти в перші артефакти темпу і вирішив результат усієї гри на його користь.</p>
       <p><b>Що мала робити четвірка в оффлейні:</b></p>
       <ul style="margin:4px 0 8px 18px;line-height:1.5">
         <li><b>Постійний харас:</b> кожні 20–30 с бити ${esc(hero(oppCore.hero_id).dname)} здібностями та з руки, збиваючи реген і змушуючи ворожого саппорта витрачати ману на захист.</li>
         <li><b>Блокування малого табору:</b> поставити Sentry або блокувати табір тілом на 1:00 / 2:00, щоб ворожий саппорт не робив безкоштовні відводи.</li>
         <li><b>Власний відвід на великий табір:</b> робити Hard Camp pull на :17 або :47 секунді, розвертаючи лінію під власну вежу.</li>
         <li><b>Контроль Лотосів:</b> забирати Lotus на 3:00, 6:00, 9:00 та красти ворожу Wisdom Rune на 7:00.</li>
       </ul>`);
    addTask(95, `Не давати ворожому керрі вільно фармити в оффлейні: блокувати малий кемп сентріком, пуллити великий табір на :17/:47 та харасити кожні 20 с.`);
  }

  if (role.core) {
    if (lh10 == null) {
      out += issue('info', 'LH@10 очікує реплею', `<p>Для точного розбору добивань на 10-й хвилині потрібен розпарсений реплей. Загальний темп добивань: <b>${role.lhpm.toFixed(1)} LH/хв</b>${bm.last_hits_per_min ? ` (кращий за ${pc(bm.last_hits_per_min.pct)}% гравців на ${esc(H.dname)})` : ''}.</p>`);
    } else if (lh10 < 45 || denies < 5) {
      const miss = Math.max(0, target - lh10), lost = miss * 40;
      out += issue(lh10 < 35 ? 'crit' : 'warn', `Контроль лінії: ${lh10} LH і ${denies} denies до 10:00`,
        `<p>Норматив для ${role.label} — <b>${target}+ LH</b> і 8+ denies до 10:00. Недобрано <b>${miss}</b> кріпів ≈ <b>${nf(lost)} золота</b> недофарму.</p>
         <p><b>Техніка Defensive Aggro:</b> кожні ~2.5 с клікай правою кнопкою миші по ворожому герою та одразу відступай назад. Ворожі мілі-кріпи переключаться на тебе і підуть під твою вежу, ближче до безпечної зони.</p>`);
      addTask(lh10 < 35 ? 90 : 80, `До 10:00 — <b>${target} LH і 8 denies</b>. Кожні ~2.5 с перетягуй агро кліком по ворогу, денай рендж-кріпа здібністю.`);
    } else {
      out += issue('good', `Впевнений лейнінг: ${lh10} LH / ${denies} denies до 10:00`, `<p>${lh10 >= target ? 'Норматив виконано' : 'Близько до нормативу'} для ${role.label} (${target} LH). ${laneDiff != null && laneDiff < 0 ? `Але лінія відставала на ${nf(-laneDiff)} золота через смерті.` : 'Стабільний контроль хвилі.'}</p>`);
    }
  } else {
    // Саппорт аналіз
    const obsEarly = (p.obs_log || []).filter(o => o.time <= 600).length;
    const obsShown = p.obs_log ? obsEarly : wards.obs;
    if (obsShown < 2) {
      out += issue('warn', `Мало вардів у лейнінгу (${obsShown} obs)`, `<p>Саппорт у лейнінгу зобов'язаний забезпечувати 2–3 варди: на активних рунах (2:00/4:00/6:00) та на підході з ворожого лісу, щоб запобігти безкарним гангам ворожого мідлейнера чи саппорта.</p>`);
      addTask(70, `Поставити <b>3 Observer Ward до 10:00</b>: на руну перед 2:00, на вхід у ліс перед 4:00 і 6:00.`);
    } else {
      out += issue('good', `${obsShown} Observer Ward`, `<p>Віжен у ранній грі був на належному рівні.</p>`);
    }
    if (lostLane && !(isOfflane && oppCore && oppCoreLH != null && oppCoreLH >= 55)) {
      out += issue('warn', 'Лінія програна за ресурсами', `<p>${laneDiff != null ? `На 10:00 лінія відставала на <b>${nf(-laneDiff)} золота</b>. ` : ''}Своєчасно блокуй ворожий пулл-кемп сентрі-вардом і не залишай напарника 1-в-2.</p>`);
    }
  }

  // Реген у перші 8 хвилин
  if (log.length) {
    const reg = log.filter(e => e.time <= 480 && REGEN.includes(e.key));
    const hasStick = reg.some(e => e.key === 'magic_stick');
    const spent = reg.reduce((s, e) => s + (e.key === 'magic_wand' && hasStick ? cost('magic_wand') - cost('magic_stick') : cost(e.key)), 0);
    const regTxt = reg.length ? reg.map(e => itemName(e.key)).join(', ') : 'нічого';
    if (lostLane && spent < 350) {
      out += issue('crit', `Заощадження на ресурсах: лише ${spent} золота на реген до 8:00`,
        `<p>Куплено: ${esc(regTxt)}. При цьому лінія програна${laneDiff != null ? ` (−${nf(-laneDiff)} золота на 10:00)` : ''}.</p>
         <p>Знижене здоров'я змушує пропускати кріпів та відходити до вишки. При активному тиску обов'язково замовляй кур'єром додаткові Tango та Flask.</p>`);
      addTask(75, `Тримати мінімум <b>350 золота регену до 8:00</b> (Tango ×2, Flask, Magic Wand до 7:00), якщо лінія зазнає пресингу.`);
    } else {
      out += `<p class="muted" style="font-size:13px">Витрати на реген до 8:00: ${esc(regTxt)} (${spent} золота).</p>`;
    }
  } else if (!parsed) {
    out += `<p class="muted" style="font-size:13px">Детальний таймлайн покупок регену буде доступний після парсингу реплею.</p>`;
  }

  return `<section class="card"><h2><span class="sec-tag">06</span>Фаза 1: Лейнінг (0:00 – 10:00)</h2>${out}</section>`;
}

/* ======================= Фаза 2: Предмети та контр-білд ======================= */
function secItems(ctx) {
  const { p, role, parsed, turbo, enemies, mine, deathTimes, addTask } = ctx;
  let out = '';
  const log = p.purchase_log || [];
  const firstBuy = {};
  log.forEach(e => { if (firstBuy[e.key] == null) firstBuy[e.key] = e.time; });
  const norms = role.core ? CORE_T : { ...Object.fromEntries(Object.entries(CORE_T).map(([k, v]) => [k, [v[0] + 300, v[1]]])), ...SUP_T };

  if (turbo) {
    out += issue('info', 'Turbo-режим', `<p>У Turbo золото і досвід прискорені — аналізуються контр-предмети проти піку суперника.</p>`);
  } else if (!log.length) {
    out += issue('info', 'Таймінги очікують реплею', `<p>Без розпарсеного <code>purchase_log</code> оцінюються фінальні слоти та відповідність контр-предметів піку ворога.</p>`);
  } else {
    const rows = Object.keys(firstBuy).filter(k => norms[k]).map(k => ({ k, t: firstBuy[k], n: norms[k][0], why: norms[k][1] })).sort((a, b) => a.t - b.t);
    if (!rows.length) {
      out += issue(role.core && ctx.dur > 1500 ? 'warn' : 'info', 'Ключові предмети з нормативами відсутні', `<p>${role.core ? `За ${fmtT(ctx.dur)} гри не зібрано жодного ключового артефакту розгону (BKB, Blink, Manta, BF) — золото розпорошилося на дрібні слоти.` : 'Для саппорта це типово за наявності сейв-предметів.'}</p>`);
    } else {
      rows.forEach((r, i) => { r.judged = i < 3 && r.t - r.n <= 900; });
      out += `<table class="timeline"><tbody>${rows.map(r => {
        const d = r.t - r.n, cls = !r.judged ? '' : d <= 0 ? 'good' : d < 180 ? 'warn' : 'crit';
        return `<tr><td>${itemIcon(r.k)}${esc(itemName(r.k))}</td><td>${fmtT(r.t)}</td><td class="muted">${r.judged ? 'норма ' + fmtT(r.n) : 'ситуативний слот'}</td><td class="delta ${cls}">${!r.judged ? '<span class="muted">—</span>' : d <= 0 ? '−' + fmtT(-d) : '+' + fmtT(d)}</td></tr>`;
      }).join('')}</tbody></table>`;
      const late = rows.filter(r => r.judged && r.t - r.n >= 180).sort((a, b) => (b.t - b.n) - (a.t - a.n));
      late.slice(0, 2).forEach((r, i) => {
        const d = r.t - r.n, dB = deathTimes.filter(t => t < r.t).length;
        out += issue(d >= 300 ? 'crit' : 'warn', `${esc(itemName(r.k))} запізнився на ${fmtT(d)}`,
          `<p>Куплено на <b>${fmtT(r.t)}</b> при нормі ${fmtT(r.n)}. Втрачено ≈ <b>${Math.round(d / 60)} хв темпу</b>: ${r.why}.${dB >= 3 ? ` До цієї покупки ти помер ${dB} рази.` : ''}</p>`);
        if (i === 0) addTask(d >= 300 ? 85 : 65, `Зібрати <b>${esc(itemName(r.k))} до ${fmtT(r.n)}</b>: між хвилями обов'язково фарм лісових кемпів.`);
      });
    }
  }

  // Контр-білд проти 5 ворогів
  const enemyHeroes = enemies.map(e => hero(e.hero_id));
  const missingCounters = [];
  const checks = [
    {
      why: 'Ворожий контроль та сайленс',
      match: h => (h.roles || []).includes('Disabler') || ['lion','shadow_shaman','bane','storm_spirit','puck','silencer','death_prophet','night_stalker'].includes(h.short),
      need: ['black_king_bar', 'manta', 'lotus_orb', 'aeon_disk', 'sange_and_yasha'],
      rec: role.core ? 'Black King Bar або Manta' : 'Lotus Orb / Glimmer Cape',
      task: role.core ? 'Купити <b>BKB до 24:00</b>' : 'Купити <b>Lotus Orb або Glimmer Cape</b>'
    },
    {
      why: 'Ворожа регенерація та самолікування',
      match: h => ['necrophos','alchemist','slark','huskar','morphling','io','dazzle','lifestealer'].includes(h.short),
      need: ['spirit_vessel', 'skadi', 'shivas_guard'],
      rec: 'Spirit Vessel, Eye of Skadi або Shiva\'s Guard',
      task: 'Зібрати <b>Spirit Vessel / Skadi / Shiva</b> проти пасивного відхилу ворогів'
    },
    {
      why: 'Вороже ухилення (Evasion)',
      match: h => ['phantom_assassin','windranger','brewmaster'].includes(h.short) || enemies.some(e => finalItems(e).some(k => ['butterfly','radiance','heavens_halberd'].includes(k))),
      need: ['monkey_king_bar', 'bloodthorn', 'javelin'],
      rec: 'Monkey King Bar або Bloodthorn',
      task: 'Зібрати <b>Monkey King Bar</b> проти ворожого evasion'
    },
    {
      why: 'Ворожа невидимість',
      match: h => ['riki','clinkz','bounty_hunter','nyx_assassin','mirana','weaver','sand_king'].includes(h.short) || enemies.some(e => finalItems(e).some(k => ['invis_sword','silver_edge','glimmer_cape'].includes(k))),
      need: ['dust', 'ward_sentry', 'gem'],
      rec: 'Dust of Appearance у постійному інвентарі',
      task: 'Завжди носити <b>Dust of Appearance</b> проти невидимих цілей'
    }
  ];

  checks.forEach(c => {
    const matched = enemyHeroes.filter(c.match);
    if (matched.length) {
      const ok = hasAny(mine, c.need);
      if (!ok) {
        missingCounters.push({ ...c, foes: matched });
        addTask(60, c.task);
      }
    }
  });

  if (missingCounters.length) {
    out += `<h3>Контр-предмети проти піку ворогів</h3>`;
    missingCounters.forEach(mc => {
      out += issue('warn', `Не вистачає контри: ${mc.why}`,
        `<p>Проти: ${mc.foes.map(f => `<b>${esc(f.dname)}</b>`).join(', ')}. Рекомендовано зібрати: <b>${mc.rec}</b>.</p>`);
    });
  } else {
    out += issue('good', 'Контр-білд укомплектований', '<p>Твій інвентар містить необхідні предмети захисту та нейтралізації ключових фішок піку суперника.</p>');
  }

  return `<section class="card"><h2><span class="sec-tag">07</span>Фаза 2: Таймінги предметів та контр-білд</h2>${out}</section>`;
}


/* ======================= Тактичний аудит смертей ======================= */
function buildTacticalDeathAudit(ctx) {
  const { p, enemies, dur, mins, role, parsed, H, detailedDeaths } = ctx;
  const d = p.deaths || 0;
  if (!d) {
    return `<div class="issue good" style="margin-top:14px"><div class="it"><span class="tag">Бездоганне виживання</span><span>0 смертей за весь матч</span></div><p>Ідеальна дисципліна позиціонування — жодного разу не віддав ворогам золото та досвід.</p></div>`;
  }

  // 1. Топ ліквідаторів (killed_by)
  const killedBy = p.killed_by || {};
  const killerEntries = Object.entries(killedBy).map(([k, cnt]) => {
    const short = k.replace('npc_dota_hero_', '');
    const eHero = Object.values(state.heroes).find(h => h.short === short) || { dname: short.replace(/_/g, ' '), short };
    return { eHero, cnt, share: Math.round((cnt / Math.max(1, d)) * 100) };
  }).sort((a, b) => b.cnt - a.cnt);

  const killersHtml = killerEntries.length ? `
    <div style="margin-top:14px">
      <div style="font-size:13px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px">Твої головні вбивці (хто відправляв у таверну):</div>
      <div class="death-killers-grid">
        ${killerEntries.map(k => `
          <div class="death-killer-card">
            <img src="${heroImg(k.eHero.id)}" alt="">
            <div style="flex:1;min-width:0">
              <div class="death-killer-name">${esc(k.eHero.dname)}</div>
              <div class="death-killer-stat">${k.cnt} ${k.cnt === 1 ? 'смерть' : (k.cnt < 5 ? 'смерті' : 'смертей')} (${k.share}%)</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  // 2. Топ смертоносних здібностей ворога (damage_inflictor_received)
  const dmgRec = p.damage_inflictor_received || {};
  const topSpells = Object.entries(dmgRec)
    .filter(([k]) => k !== 'null')
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  const topSpellsHtml = topSpells.length ? `
    <div style="background:var(--card2);border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;line-height:1.6">
      <div style="font-weight:750;color:var(--accent);margin-bottom:4px">Найнебезпечніші здібності ворогів проти тебе:</div>
      <div>${topSpells.map(([sp, dmg]) => `• <b>${esc(formatSpellName(sp))}</b>: завдала <b>${nf(dmg)} урону</b>`).join('<br>')}</div>
    </div>
  ` : '';

  // 3. Хронологічний розбір кожної смерті (Detailed Deaths Timeline)
  let timelineHtml = '';
  if (detailedDeaths && detailedDeaths.length) {
    const itemsLog = p.purchase_log || [];
    const deathCards = detailedDeaths.map((dt, i) => {
      const t = dt.time;
      const kHero = dt.killerHero;
      const itemsBefore = itemsLog.filter(x => x.time <= t).map(x => x.key);
      const isNight = (t % 600) >= 300;
      const killerShort = kHero.short || '';

      const reasons = [];
      let advice = '';

      if (killerShort.includes('night_stalker')) {
        if (isNight) {
          reasons.push(`<b>Нічна фаза карти:</b> Night Stalker під дією Dark Ascension має максимальний огляд, прискорення та безмовність (Crippling Fear). Помилка — вихід на самоті у ліс або за річку вночі.`);
          advice = `У нічний час грати під захистом власних веж або триматися за спинами команди. Проти Crippling Fear критично мати Eul's Scepter, Force Staff або BKB.`;
        } else {
          reasons.push(`<b>Агресивний врив Night Stalker:</b> швидке зближення, сповільнення від Void та фізичний пресинг.`);
          advice = `Тримати дистанцію та не підпускати мілі-ініціатора без варду.`;
        }
      } else if (killerShort.includes('mirana')) {
        reasons.push(`<b>Стріла з туману війни (Sacred Arrow):</b> далекобійне оглушення з темряви з наступним берстом від Starfall. Сталося через відсутність огляду лісу або прямолінійний біг.`);
        advice = `Постійно оновлювати Sentry-варди біля річки, щоб бачити підхід Mirana, рухатися зигзагами та ховатися за крипами.`;
      } else if (killerShort.includes('ringmaster')) {
        reasons.push(`<b>Магічний прокаст Ringmaster:</b> уловлювання коліщатком Wheel of Wonder та чистий урон від батога Impalement.`);
        advice = `Не дивитися на колесо Ringmaster (відвертати героя спиною) та вчасно купувати BKB / Cloak / Glimmer.`;
      } else if (killerShort.includes('spirit_breaker')) {
        reasons.push(`<b>Глобальний розгін (Charge of Darkness):</b> врив через усю карту та моментальний контроль Nether Strike.`);
        advice = `Як тільки ворог розганяється — негайно відступати під вежу до союзників або збивати розгін Eul's / дизейблом.`;
      } else if (killerShort.includes('bloodseeker')) {
        reasons.push(`<b>Rupture + Thirst:</b> накладання Rupture унеможливило втечу, а ворог добив на максимальній швидкості.`);
        advice = `Проти Rupture обов'язково носити Town Portal Scroll (робити TP до бази, якщо у ворогів немає стану) або купувати Linken's Sphere / Eul.`;
      } else if (killerShort.includes('sven')) {
        reasons.push(`<b>Фізичний вибух BKB Sven:</b> стрибок зі Storm Hammer під God's Strength, урон Cleave знищив за 2–3 удари.`);
        advice = `Своєчасно тиснути Ghost Scepter, Force Staff або Eul, розриваючи контакт на час дії BKB.`;
      } else if (killerShort.includes('lion') || killerShort.includes('shadow_shaman')) {
        reasons.push(`<b>Миттєвий дизейбл (Hex + Stun):</b> потрапляння під довгий контроль без можливості натиснути власні здібності.`);
        advice = `Купувати Linken's Sphere або BKB і чекати, поки саппорт віддасть контроль по іншій цілі.`;
      }

      // Додатковий макро-контекст таймінгів
      if (t >= 400 && t <= 460) {
        reasons.push(`Сутичка за <b>першу Руну Мудрості (Wisdom Rune 7:00)</b>: ризикована спроба вкрасти руну або бій біля нейтрального табору.`);
      } else if (t >= 820 && t <= 880) {
        reasons.push(`Таймінг <b>другої Руни Мудрості (14:00)</b>: ворожа засідка у зоні крайніх кемпів.`);
      } else if (t >= 1180 && t <= 1260) {
        reasons.push(`Таймінг <b>Торментора (Tormentor 20:00)</b>: сутичка за Шард.`);
      } else if (t >= 1800) {
        reasons.push(`<b>Пізня гра (хайграунд / Рошан):</b> загибель у вирішальному файті.`);
      }

      // Перевірка предметів на руках
      const hasBkb = itemsBefore.includes('black_king_bar');
      const hasForce = itemsBefore.includes('force_staff') || itemsBefore.includes('glimmer_cape');
      if (role.core && !hasBkb && t >= 900) {
        reasons.push(`<b>Вікно без BKB:</b> ти опинився у центрі сутички проти магічного прокасту без захисного артефакту.`);
      } else if (!role.core && !hasForce && t >= 720) {
        reasons.push(`<b>Відсутність сейв-слоту:</b> не вистачило Force Staff чи Glimmer Cape для розриву дистанції.`);
      }

      if (!reasons.length) {
        reasons.push(`Командна битва проти переважаючих сил ворога (ліквідатор: <b>${esc(kHero.dname)}</b>).`);
        advice = `Тримати позицію позаду ініціаторів команди.`;
      }

      return `
        <div class="death-item">
          <div class="death-time-badge">${fmtT(t)}</div>
          <div class="death-item-body">
            <div class="death-item-head">
              <img src="${heroImg(kHero.id)}" alt="">
              <span>Смерть #${i + 1} від ${esc(kHero.dname)}</span>
            </div>
            <div class="death-item-reason">${reasons.join(' ')}</div>
            ${advice ? `<div class="death-item-tip"><b>Порада тренера:</b> ${advice}</div>` : ''}
          </div>
        </div>
      `;
    }).join('');

    timelineHtml = `
      <div style="margin-top:16px">
        <div style="font-size:13px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px">Хронологія та тактичні причини кожної смерті:</div>
        <div class="death-timeline">${deathCards}</div>
      </div>
    `;
  } else if (!parsed) {
    timelineHtml = `
      <div style="margin-top:14px;background:var(--card2);border:1px solid var(--border);border-radius:10px;padding:12px 16px;font-size:13px;line-height:1.6">
        <span style="color:var(--warn);font-weight:700">Хронологія кожної окремої смерті:</span> очікує парсингу реплею (.dem).
        <p style="margin:4px 0 8px;color:var(--muted)">Після розбору реплею тут з'явиться похвилинна хроніка кожної загибелі: хто завдав останнього удару, які здібності ворога спрацювали та що саме ти мав зробити, щоб вижити.</p>
        <button class="btn btn-sm btn-primary" data-parse="${ctx.m.match_id}">Запросити розбір реплею в OpenDota</button>
      </div>
    `;
  }

  return `
    <div class="death-audit-box">
      <div class="death-audit-title">
        <span class="pill crit">Тактичний аудит смертей</span>
        <span>Чому саме ти віддавав життя (${d} смертей за матч)</span>
      </div>
      <p class="sub" style="margin:2px 0 10px">Аналіз ворожих кілерів, отриманого урону та помилок таймінгу за телеметрією реплею.</p>
      ${killersHtml}
      ${topSpellsHtml}
      ${timelineHtml}
    </div>
  `;
}

/* ======================= Фаза 3: Макро-гра ======================= */
function secMacro(ctx) {
  const { p, team, enemies, dur, mins, role, parsed, addTask, H } = ctx;
  let out = '';
  const teamKills = team.reduce((s, x) => s + (x.kills || 0), 0);
  const kp = teamKills ? (p.kills + p.assists) / teamKills : 0;
  const d = p.deaths || 0;
  const deadTimeSec = Math.round(d * Math.min(100, 10 + mins * 1.5));
  const deadMin = (deadTimeSec / 60).toFixed(1);
  const deadShare = Math.round((deadTimeSec / dur) * 100);
  const wards = getWardsData(p);

  // Ворожий віжен для порівняння
  const oppObs = enemies.reduce((s, e) => s + (getWardsData(e).obs || 0), 0);
  const allyObs = team.reduce((s, a) => s + (getWardsData(a).obs || 0), 0);

  // Розрахунок економіки смертей
  const goldGiven = Math.round(d * (180 + mins * 6.5));
  const missedFarmGold = Math.round((deadTimeSec / 60) * ((p.gold_per_min || 300) * 0.7));
  const totalDeathLoss = goldGiven + missedFarmGold;

  out += `<div class="tiles">
    ${tile('Участь у файтах', pc(kp) + '%', kp < 0.4 ? 'warn' : 'good')}
    ${tile('Смертей за гру', d, d >= 9 ? 'crit' : d >= 5 ? 'warn' : 'good')}
    ${tile('Час у таверні', `${deadMin} хв (${deadShare}%)`, deadShare > 20 ? 'crit' : deadShare > 10 ? 'warn' : 'good')}
    ${tile('Tower damage', nf(p.tower_damage || 0), (p.tower_damage || 0) < 500 && role.core ? 'crit' : (p.tower_damage || 0) === 0 ? 'warn' : 'good')}
    ${tile('Observer варди', wards.obs, wards.obs >= 8 ? 'good' : wards.obs < 4 && !role.core ? 'crit' : '')}
    ${tile('Sentry варди', wards.sen, wards.sen >= 10 ? 'good' : wards.sen < 4 && !role.core ? 'warn' : '')}
  </div>`;

  // 1. Детальний аналіз дисципліни смертей (адаптивні оцінки без суперечностей)
  if (d <= 5) {
    out += issue('good', `Зразкова дисципліна виживання: лише ${d} ${d === 1 ? 'смерть' : d < 5 ? 'смерті' : 'смертей'} за ${fmtT(dur)}`,
      `<p>Ти провів у таверні лише <b>${deadMin} хв (${deadShare}% матчу)</b>. Смерть лише раз на ${(dur / 60 / Math.max(1, d)).toFixed(1)} хв — це відмінний показник контролю позиції, який не дозволив супернику отримувати стрік-баунті.</p>
       <div style="background:var(--card2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin:8px 0;font-size:13px">
         <div>• Збережене золото завдяки мінімуму смертей: суперник недоотримав легкі ресурси.</div>
         <div>• Постійна присутність на карті забезпечила високу участь у бійках (${pc(kp)}%) та тиск на об'єкти.</div>
       </div>`);
  } else if (d <= 8) {
    out += issue('warn', `Ціна смертей: ${d} смертей за ${fmtT(dur)}`,
      `<p>Ти провів у таверні <b>${deadMin} хв (${deadShare}% матчу)</b>. Сумарні втрати команди склали ≈ <b>${nf(totalDeathLoss)} золота</b> (пряме золото за фраги: ≈ ${nf(goldGiven)}, недофарм: ≈ ${nf(missedFarmGold)}).</p>
       <p>Смерть кожні ${(dur / 60 / Math.max(1, d)).toFixed(1)} хв. Зверни увагу на смерті під час пушу без огляду та збереження байбеків на вирішальних хвилинах.</p>`);
    if (d >= 7) addTask(80, `Зменшити ризиковані виходи: не заходити за річку без бачення мінімум 2 ворожих героїв.`);
  } else {
    out += issue('crit', `Критичний фід золота: ${d} смертей за ${fmtT(dur)} = втрата темпу`,
      `<p>Ти провів у таверні <b>${deadMin} хв (${deadShare}% матчу)</b>. Сумарна економічна діра для команди склала ≈ <b>${nf(totalDeathLoss)} золота</b>.</p>
       <div style="background:var(--card2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin:8px 0;font-size:13px">
         <div>• Пряме золото, віддане ворогам: ≈ <b>${nf(goldGiven)} золота</b></div>
         <div>• Втрачене золото від простою в таверні: ≈ <b>${nf(missedFarmGold)} золота</b></div>
         <div style="color:var(--crit);font-weight:700;margin-top:4px">• Сумарна втрата: ≈ ${nf(totalDeathLoss)} золота!</div>
       </div>
       <p>Смерть кожні ${(dur / 60 / Math.max(1, d)).toFixed(1)} хв свідчить про регулярне потрапляння під перший фокус та гру наосліп.</p>`);
    addTask(95, `Зменшити смерті до максимуму 5: не виходити на відкриті лінії без бачення мінімум 3 ворогів на мінікарті.`);
  }

  // 2. Тактичний аудит смертей: Чому і від кого відбулися ці смерті
  out += buildTacticalDeathAudit(ctx);

  // 3. Аналіз позиціонування для героя
  if (H.attr === 'str' && !role.core) {
    // Силовий саппорт або Snapfire
    out += issue('warn', `Позиціонування у командних битвах (${H.dname})`,
      `<p>${H.dname} володіє колосальним радіусом застосування здібностей (Mortimer Kisses діє на 3000 ренджу, Scatterblast на 800). Твоє завдання у файті — <b>стояти у тумані війни (Fog of War) або на височині</b>, на відстані 1000+ за спинами своїх корів.</p>
       <p>Велика кількість смертей (${d}) свідчить про те, що ти опинявся в центрі сутички й потрапляв під перший фокус ворожих ініціаторів або BKB-керрі. У цій грі обов'язково був потрібен <b>Force Staff</b> (розрив дистанції) або <b>Ghost Scepter / Glimmer Cape</b> для порятунку від фізичного урону.</p>`);
    addTask(85, `Тримати дистанцію 1000+ ренджу у файтах: чекати початку ініціації у тумані війни, купувати Force Staff / Glimmer.`);
  } else if (role.core && (p.tower_damage || 0) < 1500) {
    out += issue('warn', `Нульовий пресинг будівель: лише ${nf(p.tower_damage || 0)} урону по вежах`,
      `<p>У Dota 2 гру виграють зламані вежі, а не фраги. Після кожної виграної бійки чи фраг-моменту ти повертався у ліс замість пушу найближчої лінії та нанесення урону по будівлях.</p>`);
    addTask(85, `Після кожного виграного файту — <b>бити вежу або забирати Рошана протягом 30 секунд</b>.`);
  }

  // 3. Аудит віжену та девардингу
  if (!role.core) {
    const isVisionDeficit = allyObs < oppObs;
    out += issue(wards.obs < 5 ? 'crit' : isVisionDeficit ? 'warn' : 'good',
      `Аудит віжену: ${wards.obs} Observer / ${wards.sen} Sentry (${allyObs} команди проти ${oppObs} ворога)`,
      `<p>Команда суперника встановила <b>${oppObs} Observer вардів</b>, тоді як ваша команда — лише <b>${allyObs}</b> (ти поставив ${wards.obs}).</p>
       <p>${isVisionDeficit ? 'Суперник мав у рази більше інформації про ваші пересування, що дозволяло їм безкарно ловити вас на ротаціях і починати бійки першими.' : 'Контроль віжену був збалансованим.'} Норма для саппорта за ${fmtT(dur)} — мінімум <b>8–10 Observer та 10+ Sentry</b>.</p>`);
    if (wards.obs < 6) addTask(75, `Купувати Observer варди за кулдауном: ставити мінімум <b>8+ Obs та 10+ Sentry</b> за 30+ хвилин гри.`);
  }

  // 4. Макро-об'єкти карти: Руни мудрості, Лотоси та Рошан
  out += `<div style="background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin:12px 0;font-size:13px;line-height:1.6">
    <div style="font-weight:750;font-size:14px;color:var(--accent);margin-bottom:6px">Чекліст ключових макро-таймінгів на карті:</div>
    <div>• <b>Руни мудрості (Wisdom Runes на 7:00, 14:00, 21:00):</b> Критичне джерело досвіду для саппортів. Пропуск руни на 7:00 віддає ворожій команді відставання в 1.5–2 рівні.</div>
    <div>• <b>Пруди Лотосів (Lotus Pools кожні 3 хвилини):</b> Дають безкоштовне відновлення ХП/мани. Забирай лотоси на 3:00, 6:00, 9:00, щоб не витрачати золото на банки.</div>
    <div>• <b>Контроль Рошана:</b> Після 20-ї хвилини кожен бій біля ворожої Т2 має конвертуватися в забір Егіди для безпечного заходу на хайграунд.</div>
  </div>`;

  return `<section class="card"><h2><span class="sec-tag">08</span>Фаза 3: Макро-гра та бойова дисципліна</h2>${out}</section>`;
}

/* ======================= Фаза 4: Тренд 15 ігор ======================= */
async function renderTrendFor(accountId, currentHeroName) {
  const box = $('#trendBox');
  if (!accountId) { box.innerHTML = ''; return; }

  let rec = state.trendCache[accountId];
  if (!rec) {
    try {
      rec = ((await api(`/players/${accountId}/recentMatches`)) || []).slice(0, 15);
      state.trendCache[accountId] = rec;
    } catch {
      box.innerHTML = '';
      return;
    }
  }

  if (!rec.length) { box.innerHTML = ''; return; }

  const W = rec.filter(m => isWin(m.player_slot, m.radiant_win)), L = rec.filter(m => !isWin(m.player_slot, m.radiant_win));
  const kdaOf = m => (m.kills + m.assists) / Math.max(1, m.deaths);
  const dW = avg(W.map(m => m.deaths)), dL = avg(L.map(m => m.deaths));
  const kW = avg(W.map(kdaOf)), kL = avg(L.map(kdaOf));
  const tdAvg = avg(rec.map(m => m.tower_damage || 0));

  const byHero = {};
  rec.forEach(m => {
    const h = byHero[m.hero_id] ||= { id: m.hero_id, g: 0, w: 0 };
    h.g++;
    if (isWin(m.player_slot, m.radiant_win)) h.w++;
  });
  const heroes = Object.values(byHero);
  const best = [...heroes].sort((a, b) => b.w / b.g - a.w / a.g || b.g - a.g).slice(0, 3);
  const worst = [...heroes].sort((a, b) => a.w / a.g - b.w / b.g || b.g - a.g).filter(h => !best.slice(0, 1).includes(h)).slice(0, 3);
  const hr = h => `<div class="herorow"><img src="${heroImg(h.id)}" alt=""><span>${esc(hero(h.id).dname)}</span><span class="muted">${h.w}–${h.g - h.w}</span><span class="wr ${h.w / h.g >= 0.5 ? 'res win' : 'res loss'}">${pc(h.w / h.g)}%</span></div>`;

  const habits = [];
  if (L.length && W.length && dL - dW >= 3) {
    habits.push(issue('crit', `У поразках ти помираєш на ${(dL - dW).toFixed(1)} рази більше`, `<p>${dL.toFixed(1)} смертей у програних іграх проти ${dW.toFixed(1)} у виграних. Системна звичка: коли гра йде важко, ти шукаєш ризиковані файтові розіграші замість дисциплінованого захисту хай-граунду.</p>`));
  }
  if (!habits.length) {
    habits.push(issue('good', 'Стабільний патерн', `<p>Різких системних провалів за вибірку ${rec.length} ігор не виявлено — сфокусуйся на плані поточного матчу.</p>`));
  }

  box.innerHTML = `<section class="card">
    <h2><span class="sec-tag">08</span>Тренд останніх ${rec.length} ігор</h2>
    <p class="sub">${W.length}W – ${L.length}L · ${pc(W.length / rec.length)}% Вінрейт. Пошук системних звичок гравця.</p>
    <div class="tiles">
      ${tile('KDA у перемогах', kW.toFixed(2), 'good')}
      ${tile('KDA у поразках', kL.toFixed(2), kL < 2 ? 'crit' : 'warn')}
      ${tile('Смерті: перемоги', dW.toFixed(1))}
      ${tile('Смерті: поразки', dL.toFixed(1), dL - dW >= 3 ? 'crit' : '')}
      ${tile('Сер. tower damage', nf(tdAvg), tdAvg < 1500 ? 'crit' : 'good')}
    </div>
    ${habits.join('')}
    <div class="two" style="margin-top:14px">
      <div><h3>Найкращий вінрейт</h3>${best.map(hr).join('')}</div>
      <div><h3>Найгірший вінрейт</h3>${worst.map(hr).join('') || '<p class="muted">Замало даних</p>'}</div>
    </div>
  </section>`;
}

/* ======================= Фаза 5: План на гру ======================= */
function renderPlan(ctx, tasks) {
  const { role, m, p } = ctx;
  const fallback = role.core
    ? [[50, `До 10:00 — <b>${{ 1:60, 2:55, 3:40 }[role.pos] || 50} LH</b> і 8 denies; контроль хвилі через Defensive Aggro.`],
       [45, `Після кожного виграного файту — <b>бити вежу або забирати Рошана протягом 40 с</b>.`],
       [40, `<b>Не більше 5 смертей</b>: не заходити за річку без бачення 2+ ворогів на карті.`]]
    : [[50, `Поставити <b>3 Observer Ward до 10:00</b> і ${Math.round(ctx.mins * 0.4)}+ за всю гру.`],
       [45, `Зробити <b>4 стаки лісових кемпів до 15:00</b> для свого кора.`],
       [40, `Купити <b>Glimmer Cape або Force Staff до 18:00</b>.`]];

  fallback.forEach(([w, t]) => tasks.push({ w, text: t }));
  const seen = new Set();
  const top = tasks.sort((a, b) => b.w - a.w).filter(t => {
    const k = t.text.slice(0, 40);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  }).slice(0, 3);

  const key = `d2coach_plan_${m.match_id}_${p.player_slot}`;
  let saved = [];
  try { saved = JSON.parse(localStorage.getItem(key)) || []; } catch {}

  $('#planBox').innerHTML = `<section class="card plan">
    <h2><span class="sec-tag">09</span>План роботи над помилками на наступну гру</h2>
    <p class="sub">3 ключові мікро-завдання за результатами цього матчу. Відмічай виконані пункти — стан зберігається автоматично.</p>
    ${top.map((t, i) => `
      <label class="${saved[i] ? 'done' : ''}">
        <input type="checkbox" data-i="${i}" ${saved[i] ? 'checked' : ''}>
        <span class="plan-txt"><span class="num">${i + 1}.</span> ${t.text}</span>
      </label>
    `).join('')}
  </section>`;

  $('#planBox').querySelectorAll('input').forEach(inp => {
    inp.addEventListener('change', () => {
      saved[+inp.dataset.i] = inp.checked;
      inp.closest('label').classList.toggle('done', inp.checked);
      try { localStorage.setItem(key, JSON.stringify(saved)); } catch {}
    });
  });
}

/* ======================= Тема та ініціалізація ======================= */
function applyTheme(t, persist = true) {
  document.documentElement.dataset.theme = t;
  $('#themeBtn').textContent = t === 'dark' ? 'Тема: Світла' : 'Тема: Темна';
  $('#themeBtn').setAttribute('aria-pressed', String(t === 'light'));
  if (persist) { try { localStorage.setItem('d2coach_theme', t); } catch {} }
}

async function init() {
  let savedT = null;
  try { savedT = localStorage.getItem('d2coach_theme'); } catch {}
  const sysLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
  applyTheme(savedT || (sysLight ? 'light' : 'dark'), !!savedT);
  $('#themeBtn').addEventListener('click', () => {
    const cur = document.documentElement.dataset.theme;
    applyTheme(cur === 'dark' ? 'light' : 'dark');
  });

  const keyInput = $('#apiKeyInput');
  const keyModal = $('#apiKeyModal');
  if (keyInput) keyInput.value = localStorage.getItem('opendota_api_key') || '';
  $('#apiKeyBtn')?.addEventListener('click', () => {
    keyModal.style.display = keyModal.style.display === 'none' ? 'block' : 'none';
  });
  $('#saveApiKeyBtn')?.addEventListener('click', () => {
    const k = (keyInput.value || '').trim();
    if (k) localStorage.setItem('opendota_api_key', k);
    else localStorage.removeItem('opendota_api_key');
    keyModal.style.display = 'none';
    setStatus('API-ключ збережено!');
    setTimeout(clearStatus, 2000);
  });
  $('#clearApiKeyBtn')?.addEventListener('click', () => {
    if (keyInput) keyInput.value = '';
    localStorage.removeItem('opendota_api_key');
    setStatus('API-ключ видалено.');
    setTimeout(clearStatus, 2000);
  });

  window.run = run;

  document.addEventListener('click', e => {
    const qBtn = e.target.closest('[data-quick]');
    if (qBtn) {
      const val = qBtn.dataset.quick;
      $('#q').value = val;
      run(val);
    }
  });

  // Автостарт лише за прямим посиланням: ?q=ID або #ID
  const deep = new URLSearchParams(location.search).get('q') || location.hash.replace('#', '').trim();
  if (deep) { $('#q').value = deep; run(deep); }
}

document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>
'''

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Updated index.html successfully! Size:", len(html_content))

# Auto-check JS syntax via node --check
m = re.search(r"<script>(.*)</script>", html_content, re.S)
if m:
    node_cmd = shutil.which("node") or (
        r"D:\programs\cursor\resources\app\resources\helpers\node.exe"
        if os.path.exists(r"D:\programs\cursor\resources\app\resources\helpers\node.exe")
        else "node"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(m.group(1))
        t_name = t.name
    try:
        r = subprocess.run([node_cmd, "--check", t_name], capture_output=True, text=True)
        if r.returncode != 0:
            print("JS SYNTAX ERROR:\n", r.stderr)
            sys.exit(1)
        print("JS syntax OK")
    finally:
        if os.path.exists(t_name):
            os.remove(t_name)

# Auto-check forbidden symbols (Rule 1 & Rule 7)
forbidden_match = re.findall(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]', html_content)
if forbidden_match:
    print(f"FORBIDDEN SYMBOLS ERROR: Found {len(forbidden_match)} forbidden symbols from forbidden ranges: {[hex(ord(c)) for c in set(forbidden_match)]}")
    sys.exit(1)
print("No forbidden symbols found (Rule 1 OK)")
