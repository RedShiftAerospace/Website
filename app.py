import os
import json
import uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "redshift_secret_aerospace_key")

DATA_FILE = os.path.join(app.root_path, 'data.json')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'redshift_secure_2026')

STATIC_FOLDER = '/home/teslashock/public_html/static'
app.config['UPLOAD_BASE'] = STATIC_FOLDER


def load_data():
    default_structure = {
        "sponsors": [
            {"id": "sp_1", "name": "Rospin", "img": "assets/Sponsori/Rospin.avif"},
            {"id": "sp_2", "name": "UBB Physics", "img": "assets/Sponsori/UBBFizica.avif"},
            {"id": "sp_3", "name": "ASF UBB", "img": "assets/Sponsori/ASFUBB.avif"},
            {"id": "sp_4", "name": "Carfil", "img": "assets/Sponsori/carfilogo.avif"},
            {"id": "sp_5", "name": "Microchip", "img": "assets/Sponsori/Microcip.avif"}
        ],
        "team_categories": {
            "mentors": "Mentors",
            "leaders": "Team Leaders",
            "members": "Active Members",
            "alumni": "Alumns"
        },
        "team": {"mentors": [], "leaders": [], "members": [], "alumni": []},
        "timeline": [],
        "projects": [],
        "technical_groups": {
            "euroc2026": "EuRoC 2026",
            "euroc2025": "EuRoC 2025",
            "cansat": "CanSat 2024 & 2023"
        },
        "technical": {"euroc2026": [], "euroc2025": [], "cansat": []},
        "recruitment_link": "https://forms.gle/exemplu",
        "statut_pdf_path": "assets/pdfs/statut.pdf",
        "statut_visible": True,
        "socials": [
            {"id": "soc_1", "platform": "LinkedIn",
             "url": "https://www.linkedin.com/company/redshift-aerospace-industries/", "icon": "linkedin.svg"},
            {"id": "soc_2", "platform": "GitHub", "url": "https://github.com/RedShiftAerospace", "icon": "github.svg"},
            {"id": "soc_3", "platform": "Instagram", "url": "https://www.instagram.com/redshiftaero/", "icon": "instagram.svg"}
        ]
    }

    if not os.path.exists(DATA_FILE):
        return default_structure

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return default_structure

    if 'sponsors' not in data: data['sponsors'] = default_structure['sponsors']
    if 'team_categories' not in data: data['team_categories'] = default_structure['team_categories']
    if 'socials' not in data: data['socials'] = default_structure['socials']
    if 'technical_groups' not in data or not data['technical_groups']: data['technical_groups'] = default_structure['technical_groups']
    if 'technical' not in data: data['technical'] = default_structure['technical']
    if 'recruitment_link' not in data: data['recruitment_link'] = default_structure['recruitment_link']
    if 'statut_pdf_path' not in data: data['statut_pdf_path'] = default_structure['statut_pdf_path']
    if 'statut_visible' not in data: data['statut_visible'] = default_structure['statut_visible']

    for key in ["team", "timeline", "projects"]:
        if key not in data: data[key] = default_structure[key]

    return data


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_existing_folders():
    assets_dir = os.path.join(STATIC_FOLDER, 'assets')
    folder_list = ['assets/Sponsori', 'assets/Membri', 'assets/Mentori', 'assets/Galerie', 'assets/images']
    if os.path.exists(assets_dir):
        for root, dirs, files in os.walk(assets_dir):
            for d in dirs:
                full_path = os.path.join(root, d)
                relative_path = os.path.relpath(full_path, STATIC_FOLDER)
                clean_path = relative_path.replace('\\', '/')
                if clean_path not in folder_list:
                    folder_list.append(clean_path)
    return sorted(list(set(folder_list)))


@app.route('/')
def index():
    data = load_data()
    return render_template('home.html',
                           sponsors=data.get('sponsors', []),
                           team_categories=data.get('team_categories', {}),
                           team=data.get('team', {}),
                           timeline=data.get('timeline', []),
                           projects=data.get('projects', []),
                           technical=data.get('technical', {}),
                           tech_groups=data.get('technical_groups', {}),
                           recruitment_link=data.get('recruitment_link', '#'),
                           statut_pdf_path=data.get('statut_pdf_path', ''),
                           statut_visible=data.get('statut_visible', True),
                           socials=data.get('socials', []))


@app.route('/statut.html')
def statut():
    data = load_data()
    if not data.get('statut_visible', True): return redirect(url_for('index'))
    return redirect(url_for('static', filename=data.get('statut_pdf_path', 'assets/pdfs/statut.pdf')))


@app.route('/regulation.html')
def regulation():
    return render_template('regulation.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    password = request.form.get('password') if request.method == 'POST' else request.args.get('password')
    if password == ADMIN_PASSWORD:
        data = load_data()
        return render_template('admin.html',
                               sponsors=data.get('sponsors', []),
                               team_categories=data.get('team_categories', {}),
                               team=data.get('team', {}),
                               timeline=data.get('timeline', []),
                               projects=data.get('projects', []),
                               technical=data.get('technical', {}),
                               tech_groups=data.get('technical_groups', {}),
                               recruitment_link=data.get('recruitment_link', ''),
                               statut_pdf_path=data.get('statut_pdf_path', ''),
                               statut_visible=data.get('statut_visible', True),
                               socials=data.get('socials', []),
                               scanned_folders=get_existing_folders(),
                               password=password)
    if request.method == 'POST' or password: return "Parola incorecta!", 403
    return render_template('admin_login.html')


# ================= API ENDPOINT PENTRU FILE EXPLORER =================
@app.route('/admin/api/list_files')
def list_files_api():
    password = request.args.get('password')
    if password != ADMIN_PASSWORD: return jsonify({"error": "Unauthorized"}), 403
    target_folder = request.args.get('folder', '').strip().lstrip('/')
    if not target_folder: return jsonify({"files": []})
    full_path = os.path.join(STATIC_FOLDER, target_folder)
    if not os.path.exists(full_path) or not os.path.isdir(full_path): return jsonify({"files": []})
    try:
        files = [f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))]
        return jsonify({"files": sorted(files)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= SPONSORS HUB =================
@app.route('/admin/sponsors/add', methods=['POST'])
def add_sponsor():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    img_path = request.form.get('img', '').strip().lstrip('/')
    data['sponsors'].append({
        "id": str(uuid.uuid4())[:8],
        "name": request.form.get('name').strip(),
        "img": img_path if img_path else "assets/Sponsori/default.avif"
    })
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="sponsors-sec"))


@app.route('/admin/sponsors/edit/<sp_id>', methods=['POST'])
def edit_sponsor(sp_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    img_path = request.form.get('img', '').strip().lstrip('/')
    for s in data.get('sponsors', []):
        if s['id'] == sp_id:
            s['name'] = request.form.get('name').strip()
            s['img'] = img_path if img_path else "assets/Sponsori/default.avif"
            break
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="sponsors-sec"))


@app.route('/admin/sponsors/delete/<sp_id>', methods=['POST'])
def delete_sponsor(sp_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    data['sponsors'] = [s for s in data.get('sponsors', []) if s['id'] != sp_id]
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="sponsors-sec"))


# ================= ASSETS UPLOAD HUB =================
@app.route('/admin/upload_asset', methods=['POST'])
def upload_asset():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    target_folder = request.form.get('target_folder', 'assets/general').strip()
    file = request.files.get('file_asset')
    if file and target_folder:
        filename = secure_filename(file.filename)
        destination_dir = os.path.join(app.config['UPLOAD_BASE'], target_folder.strip('/'))
        os.makedirs(destination_dir, exist_ok=True)
        file.save(os.path.join(destination_dir, filename))
        computed_path = f"{target_folder.strip('/')}/{filename}"
        return f'''
        <body style="background:#000; color:#fff; font-family:sans-serif; padding:20px; text-align:center;">
            <h3 style="color:#457b9d;">File uploaded successfully!</h3>
            <p>Paste this string into the form field:</p>
            <input type="text" value="{computed_path}" style="padding:10px; width:80%; background:#111; color:#fff; border:1px solid #333; text-align:center;" readonly><br><br>
            <button onclick="if(window.opener && !window.opener.closed) {{ window.opener.location.reload(); }} window.close();" style="padding:10px 20px; background:#e63946; color:#fff; border:none; cursor:pointer; font-weight:bold;">Close & Refresh Admin</button>
        </body>
        '''
    return "Upload failed.", 400


# ================= CONFIGURATIONS SYSTEM =================
@app.route('/admin/statut/update', methods=['POST'])
def update_statut_path():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    data['statut_pdf_path'] = request.form.get('statut_pdf_path').strip()
    data['statut_visible'] = True if request.form.get('statut_visible') else False
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="statut-config-sec"))


@app.route('/admin/recruitment/update', methods=['POST'])
def update_recruitment():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    data['recruitment_link'] = request.form.get('recruitment_link').strip()
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="recruitment-config-sec"))


# ================= TEAM ROSTER ENGINE =================
@app.route('/admin/team/add_category', methods=['POST'])
def add_team_category():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    cat_key = request.form.get('cat_key').strip().lower().replace(" ", "_")
    cat_title = request.form.get('cat_title').strip()
    data = load_data()
    data.setdefault('team_categories', {})[cat_key] = cat_title
    data.setdefault('team', {}).setdefault(cat_key, [])
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="team-sec"))


@app.route('/admin/team/delete_category/<cat_key>', methods=['POST'])
def delete_team_category(cat_key):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    if cat_key in data.get('team_categories', {}): del data['team_categories'][cat_key]
    if cat_key in data.get('team', {}): del data['team'][cat_key]
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="team-sec"))


@app.route('/admin/team/add', methods=['POST'])
def add_team_member():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    category = request.form.get('category')
    data = load_data()
    data.setdefault('team', {}).setdefault(category, []).append({
        "id": str(uuid.uuid4())[:8],
        "name": request.form.get('name'),
        "role": request.form.get('role', 'Member'),
        "bio": request.form.get('bio'),
        "img": request.form.get('img', 'assets/Membri/default.avif'),
        "linkedin": request.form.get('linkedin', '')
    })
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="team-sec"))


@app.route('/admin/team/edit/<current_category>/<member_id>', methods=['POST'])
def edit_team_member(current_category, member_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    new_category = request.form.get('new_category')
    data = load_data()
    member_to_move = None
    if current_category in data.get('team', {}):
        for m in data['team'][current_category]:
            if m['id'] == member_id:
                m['name'] = request.form.get('name')
                m['role'] = request.form.get('role')
                m['bio'] = request.form.get('bio')
                m['img'] = request.form.get('img')
                m['linkedin'] = request.form.get('linkedin')
                member_to_move = m
                break
        if member_to_move and current_category != new_category:
            data['team'][current_category] = [m for m in data['team'][current_category] if m['id'] != member_id]
            data.setdefault('team', {}).setdefault(new_category, []).append(member_to_move)
        save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="team-sec"))


@app.route('/admin/team/delete/<category>/<member_id>', methods=['POST'])
def delete_team_member(category, member_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    if category in data.get('team', {}):
        data['team'][category] = [m for m in data['team'][category] if m['id'] != member_id]
        save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="team-sec"))


# ================= GLOBAL REORDER ENGINE =================
@app.route('/admin/reorder/<section>/<item_id>/<direction>', methods=['POST'])
def reorder_items(section, item_id, direction):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    target_list = None
    anchor_id = "projects-sec"
    if section in data.get('team', {}):
        target_list = data['team'][section]
        anchor_id = "team-sec"
    elif section == 'projects':
        target_list = data['projects']
        anchor_id = "projects-sec"
    elif section == 'timeline':
        target_list = data['timeline']
        anchor_id = "timeline-sec"
    elif section in data.get('technical', {}):
        target_list = data['technical'][section]
        anchor_id = f"layout-{section}"

    if target_list:
        idx = next((i for i, item in enumerate(target_list) if item['id'] == item_id), None)
        if idx is not None:
            if direction == 'up' and idx > 0: target_list[idx], target_list[idx - 1] = target_list[idx - 1], target_list[idx]
            elif direction == 'down' and idx < len(target_list) - 1: target_list[idx], target_list[idx + 1] = target_list[idx + 1], target_list[idx]
        save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor=anchor_id))


# ================= PROJECTS HUB (BILINGV ACUM) =================
@app.route('/admin/projects/add', methods=['POST'])
def add_project():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    data['projects'].append({
        "id": str(uuid.uuid4())[:8],
        "title": request.form.get('title'),
        "class_attr": request.form.get('class_attr', ''),
        "image": request.form.get('image', ''),
        "content_en": request.form.get('content_en', ''),
        "content_ro": request.form.get('content_ro', '')
    })
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="projects-sec"))


@app.route('/admin/projects/edit/<project_id>', methods=['POST'])
def edit_project(project_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    for p in data['projects']:
        if p['id'] == project_id:
            p['title'] = request.form.get('title')
            p['class_attr'] = request.form.get('class_attr', '')
            p['image'] = request.form.get('image', '')
            p['content_en'] = request.form.get('content_en', '')
            p['content_ro'] = request.form.get('content_ro', '')
            break
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="projects-sec"))


@app.route('/admin/projects/delete/<project_id>', methods=['POST'])
def delete_project(project_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    data['projects'] = [p for p in data['projects'] if p['id'] != project_id]
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="projects-sec"))


# ================= TECHNICAL REPERTOIRE =================
@app.route('/admin/technical/add_group', methods=['POST'])
def add_tech_group():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    group_key = request.form.get('group_key').strip().lower().replace(" ", "_")
    group_title = request.form.get('group_title').strip()
    data = load_data()
    data.setdefault('technical_groups', {})[group_key] = group_title
    data.setdefault('technical', {})[group_key] = []
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="tech-sec"))


@app.route('/admin/technical/delete_group/<group_key>', methods=['POST'])
def delete_tech_group(group_key):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    if group_key in data.get('technical_groups', {}): del data['technical_groups'][group_key]
    if group_key in data.get('technical', {}): del data['technical'][group_key]
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="tech-sec"))


@app.route('/admin/technical/add', methods=['POST'])
def add_technical():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    group = request.form.get('group')
    data = load_data()
    data.setdefault('technical', {}).setdefault(group, []).append({
        "id": str(uuid.uuid4())[:8],
        "name": request.form.get('name'),
        "badge": request.form.get('badge', 'PDF'),
        "path": request.form.get('path')
    })
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor=f"layout-{group}"))


@app.route('/admin/technical/edit/<group>/<doc_id>', methods=['POST'])
def edit_technical(group, doc_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    for d in data['technical'].get(group, []):
        if d['id'] == doc_id:
            d['name'] = request.form.get('name')
            d['badge'] = request.form.get('badge')
            d['path'] = request.form.get('path')
            break
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor=f"layout-{group}"))


@app.route('/admin/technical/delete/<group>/<doc_id>', methods=['POST'])
def delete_technical(group, doc_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    if group in data.get('technical', {}):
        data['technical'][group] = [d for d in data['technical'][group] if d['id'] != doc_id]
        save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor=f"layout-{group}"))


# ================= TIMELINE DE-DUPLICATE SYSTEM =================
@app.route('/admin/timeline/add', methods=['POST'])
def add_timeline():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    date_input = request.form.get('date').strip()
    event_type = request.form.get('event_type')
    event_text = request.form.get('event_text').strip()
    image_input = request.form.get('image', '').strip()
    data = load_data()
    timeline = data.setdefault('timeline', [])
    existing_entry = next((item for item in timeline if item['date'] == date_input), None)
    new_event = {"sub_id": str(uuid.uuid4())[:8], "type": event_type, "text": event_text}
    if existing_entry:
        existing_entry['events'].append(new_event)
        if image_input and not existing_entry.get('image'): existing_entry['image'] = image_input
    else:
        timeline.insert(0, {
            "id": str(uuid.uuid4())[:8],
            "date": date_input,
            "image": image_input if image_input else "",
            "events": [new_event]
        })
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="timeline-sec"))


@app.route('/admin/timeline/edit_root/<entry_id>', methods=['POST'])
def edit_timeline_root(entry_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    for entry in data.get('timeline', []):
        if entry['id'] == entry_id:
            entry['date'] = request.form.get('date').strip()
            entry['image'] = request.form.get('image', '').strip()
            break
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="timeline-sec"))


@app.route('/admin/timeline/edit_sub/<entry_id>/<sub_id>', methods=['POST'])
def edit_timeline_sub_event(entry_id, sub_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    for entry in data.get('timeline', []):
        if entry['id'] == entry_id:
            for ev in entry.get('events', []):
                if ev.get('sub_id') == sub_id:
                    ev['type'] = request.form.get('event_type')
                    ev['text'] = request.form.get('event_text').strip()
                    break
            break
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="timeline-sec"))


@app.route('/admin/timeline/delete_sub/<entry_id>/<sub_id>', methods=['POST'])
def delete_timeline_sub_event(entry_id, sub_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    for entry in data.get('timeline', []):
        if entry['id'] == entry_id:
            entry['events'] = [ev for ev in entry['events'] if ev.get('sub_id') != sub_id]
            if not entry['events']: data['timeline'] = [e for e in data['timeline'] if e['id'] != entry_id]
            break
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="timeline-sec"))


# ================= SOCIAL CHANNELS MANAGER =================
@app.route('/admin/socials/add', methods=['POST'])
def add_social():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    data['socials'].append({
        "id": str(uuid.uuid4())[:8],
        "platform": request.form.get('platform').strip(),
        "url": request.form.get('url').strip(),
        "icon": request.form.get('icon').strip() or "link.svg"
    })
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="socials-config-sec"))


@app.route('/admin/socials/edit/<soc_id>', methods=['POST'])
def edit_social(soc_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    for s in data.get('socials', []):
        if s['id'] == soc_id:
            s['platform'] = request.form.get('platform').strip()
            s['url'] = request.form.get('url').strip()
            s['icon'] = request.form.get('icon').strip() or "link.svg"
            break
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="socials-config-sec"))


@app.route('/admin/socials/delete/<social_id>', methods=['POST'])
def delete_social(social_id):
    password = request.form.get('password')
    if password != ADMIN_PASSWORD: return "Neautorizat", 403
    data = load_data()
    data['socials'] = [s for s in data['socials'] if s['id'] != social_id]
    save_data(data)
    return redirect(url_for('admin_panel', password=password, _anchor="socials-config-sec"))


@app.route('/static/assets/pdfs/<path:filename>')
def serve_pdfs(filename):
    return send_from_directory(STATIC_FOLDER, os.path.join('assets', 'pdfs', filename))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)