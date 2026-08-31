import os
import glob
import re

PAGES = [
    {
        "file": "frontend/dashboard.html",
        "key": "dashboard",
        "title": "Operations Dashboard | RAILOPT"
    },
    {
        "file": "frontend/index.html",
        "key": "dashboard",
        "title": "Operations Dashboard | RAILOPT"
    },
    {
        "file": "frontend/maintenance-requests.html",
        "key": "maintenance-requests",
        "title": "Maintenance Requests | RAILOPT"
    },
    {
        "file": "frontend/block-planning.html",
        "key": "block-planning",
        "title": "Block Planning & Optimization | RAILOPT"
    },
    {
        "file": "frontend/gantt-view.html",
        "key": "gantt-view",
        "title": "Corridor Gantt Timeline | RAILOPT"
    },
    {
        "file": "frontend/what-if.html",
        "key": "what-if",
        "title": "What-If Scenario Simulation | RAILOPT"
    },
    {
        "file": "frontend/constraints-logic.html",
        "key": "constraints-logic",
        "title": "Plan Logic & Constraints | RAILOPT"
    },
    {
        "file": "frontend/reports.html",
        "key": "reports",
        "title": "Operational Reports & Analytics | RAILOPT"
    }
]

NAV_ITEMS = [
    {"href": "/dashboard", "id": "nav-dashboard", "icon": "dashboard", "label": "Operations Dashboard", "key": "dashboard"},
    {"href": "/maintenance-requests", "id": "nav-maintenance-requests", "icon": "pending_actions", "label": "Maintenance Requests", "key": "maintenance-requests"},
    {"href": "/block-planning", "id": "nav-block-planning", "icon": "edit_calendar", "label": "Block Planning", "key": "block-planning"},
    {"href": "/gantt-view", "id": "nav-gantt-view", "icon": "view_timeline", "label": "Gantt View", "key": "gantt-view"},
    {"href": "/what-if", "id": "nav-what-if", "icon": "query_stats", "label": "What-if Analysis", "key": "what-if"},
    {"href": "/constraints-logic", "id": "nav-constraints-logic", "icon": "rule", "label": "Plan Logic & Constraints", "key": "constraints-logic"},
    {"href": "/reports", "id": "nav-reports", "icon": "assessment", "label": "Reports", "key": "reports"}
]

def generate_sidebar(active_key):
    items_html = []
    for item in NAV_ITEMS:
        is_active = (item["key"] == active_key)
        if is_active:
            link_cls = "flex items-center gap-sm px-md py-sm rounded-lg bg-primary-container text-on-primary-container border-l-4 border-on-primary-container font-semibold transition-all duration-150 active:scale-[0.98]"
            span_cls = "font-label-md text-label-md"
        else:
            link_cls = "flex items-center gap-sm px-md py-sm rounded-lg text-on-primary-container opacity-70 hover:bg-primary-container hover:opacity-100 transition-all duration-150 active:scale-[0.98]"
            span_cls = "font-label-md text-label-md"
        
        items_html.append(f'''        <li class="sidebar-item">
            <a class="{link_cls}" href="{item['href']}" id="{item['id']}">
                <span class="material-symbols-outlined text-[20px]">{item['icon']}</span>
                <span class="{span_cls}">{item['label']}</span>
            </a>
        </li>''')

    nav_list = "\n".join(items_html)

    return f'''<!-- Standardized SideNavBar (Desktop) -->
<nav class="hidden md:flex flex-col py-md w-[240px] h-screen fixed left-0 top-0 z-40 bg-primary dark:bg-tertiary">
    <div class="px-md mb-lg">
        <a href="/dashboard" class="flex items-center gap-sm mb-xs cursor-pointer">
            <img src="/assets/10_indian_railways_official_logo_ad892ab5.png" alt="Indian Railways Official Logo" class="w-9 h-9 rounded-full bg-white p-0.5 shadow-sm object-cover">
            <div>
                <h1 class="font-headline-sm text-[17px] font-bold text-on-primary uppercase tracking-tight leading-none">RAILOPT</h1>
                <p class="font-body-sm text-[11px] text-on-primary opacity-80 mt-0.5">Block Planning System</p>
            </div>
        </a>
    </div>
    <div class="flex-1 overflow-y-auto dense-scroll">
        <ul class="flex flex-col gap-xs px-sm">
{nav_list}
        </ul>
    </div>
    <div class="mt-auto px-sm pt-md border-t border-primary-container">
        <ul class="flex flex-col gap-xs">
            <li>
                <button onclick="window.triggerNewRequestModal && window.triggerNewRequestModal()" class="w-full flex items-center gap-sm px-md py-sm rounded-lg bg-surface-tint text-on-primary font-semibold hover:bg-opacity-90 transition-all shadow-sm">
                    <span class="material-symbols-outlined text-[20px]">add_circle</span>
                    <span class="font-label-md text-label-md">New Request</span>
                </button>
            </li>
            <li>
                <a class="flex items-center gap-sm px-md py-sm rounded-lg text-on-primary-container opacity-70 hover:bg-primary-container hover:opacity-100 transition-all duration-150" href="/constraints-logic">
                    <span class="material-symbols-outlined text-[20px]">verified_user</span>
                    <span class="font-label-md text-label-md">Domain Rules</span>
                </a>
            </li>
        </ul>
    </div>
</nav>'''

def generate_headers():
    return '''<!-- Standardized TopNavBar (Mobile) -->
<header class="flex md:hidden justify-between items-center px-md w-full fixed top-0 z-50 bg-primary border-b border-outline-variant h-16">
    <div class="flex items-center gap-sm">
        <img alt="Indian Railways Official Logo" class="w-8 h-8 rounded-full bg-white p-0.5 object-cover" src="/assets/10_indian_railways_official_logo_ad892ab5.png">
        <span class="font-headline-md text-headline-md font-bold text-on-primary tracking-tight uppercase">RAILOPT</span>
    </div>
    <div class="flex items-center gap-sm text-on-primary">
        <button class="hover:bg-primary-container p-1.5 rounded-full"><span class="material-symbols-outlined text-[20px]">notifications</span></button>
        <div class="flex items-center gap-1.5 bg-primary-container px-2.5 py-1 rounded-lg">
            <span class="font-label-md text-label-md text-on-primary">Planner</span>
        </div>
    </div>
</header>

<!-- Standardized Desktop Header -->
<header class="hidden md:flex justify-between items-center px-lg w-full h-16 bg-primary border-b border-primary-container z-30 fixed top-0 left-[240px] right-0" style="width: calc(100% - 240px);">
    <div class="flex items-center gap-sm">
        <span class="font-body-sm text-body-sm text-on-primary opacity-90 font-medium">AI-Powered Block Planning System</span>
        <span class="text-xs bg-primary-container text-on-primary px-2 py-0.5 rounded text-[11px] border border-outline-variant/30">Northern / NCR Division</span>
    </div>
    <div class="flex items-center gap-lg">
        <span class="font-label-md text-label-md text-on-primary opacity-80" id="header-datetime">31 Aug 2026 | 20:15:00</span>
        <div class="flex items-center gap-sm text-on-primary">
            <button class="hover:bg-primary-container p-1.5 rounded-full transition-colors duration-200 relative" title="Notifications">
                <span class="material-symbols-outlined text-[20px]">notifications</span>
                <span class="absolute top-1 right-1 w-2 h-2 bg-error rounded-full"></span>
            </button>
            <a href="/constraints-logic" class="hover:bg-primary-container p-1.5 rounded-full transition-colors duration-200" title="Configuration & Rules">
                <span class="material-symbols-outlined text-[20px]">settings</span>
            </a>
        </div>
        <div class="flex items-center gap-2 bg-primary-container px-3 py-1.5 rounded-lg border border-outline-variant/20">
            <div class="w-6 h-6 rounded-full bg-surface text-primary flex items-center justify-center font-bold text-xs">P</div>
            <span class="font-label-md text-label-md text-on-primary font-medium">Planner</span>
            <span class="material-symbols-outlined text-[16px] text-on-primary opacity-70">expand_more</span>
        </div>
    </div>
</header>'''

def standardize_page(filepath, active_key, title):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Title
    content = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', content, flags=re.DOTALL)

    # 2. Extract <head>...</head> and script tags at bottom
    # Replace anything between <body ...> and <main ...>
    body_match = re.search(r'(<body[^>]*>)', content)
    main_match = re.search(r'(<main[^>]*>)', content)
    
    if not body_match or not main_match:
        print(f"[!] Could not find body/main in {filepath}")
        return

    body_tag = '<body class="font-body-md text-on-surface bg-background flex flex-col md:flex-row min-h-screen overflow-x-hidden">'
    main_tag = '<main class="flex-1 md:ml-[240px] mt-16 p-container-margin md:p-lg bg-surface-container-lowest min-h-screen">'

    sidebar_html = generate_sidebar(active_key)
    header_html = generate_headers()

    top_section = content[:body_match.start()]
    main_section_start = main_match.end()
    rest_of_content = content[main_section_start:]

    # Remove stray loose numbers at beginning of main (e.g. 16 or 17/16)
    rest_of_content = re.sub(r'^\s*<div[^>]*>\s*(?:16|17/16|\d+/\d+)\s*</div>', '', rest_of_content, flags=re.MULTILINE)
    rest_of_content = re.sub(r'^\s*(?:16|17/16|\d+/\d+)\s*\n', '', rest_of_content, flags=re.MULTILINE)

    new_content = f"{top_section}{body_tag}\n{sidebar_html}\n{header_html}\n{main_tag}\n{rest_of_content}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[+] Successfully standardized {filepath} (active: {active_key})")

for p in PAGES:
    standardize_page(p["file"], p["key"], p["title"])

print("All pages standardized!")

