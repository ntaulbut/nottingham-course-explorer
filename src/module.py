from datetime import datetime, timezone

from flask import abort, render_template

from config import FEATURE_FLAGS
from tools import add_column_names, get_db, parse_table, num_to_word


def format_class(class_type: str, weeks: str, per_week_str: str, duration: str) -> str:
    duration = (duration
                .replace("hours", "hour")
                .replace("minutes", "minute")
                .replace(" ", "-")) + " " if duration != "" else ""
    if weeks == "1 week":
        return f"One {duration}{class_type.lower()}"
    per_week = int(per_week_str.split(" ")[0])
    return f"{num_to_word(per_week).title()} {duration}{class_type.lower()}{'s' if per_week > 1 else ''} per week for {weeks}"


def format_assessment(title: str, weight: str, type_: str, duration: str, requirements: str) -> str:
    weight = f"{int(float(weight))}% " if weight.strip() else ""
    if duration.strip():
        duration_str = " (" + (duration.replace("Hr", "-hour")
                               .replace("Mins", "-minute")
                               .replace(" ", "-")) + ")"
    else:
        duration_str = ""
    requirements_str = ": " + requirements if requirements else ""
    return weight + title + duration_str + requirements_str


def module_page(code: str = None):
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM modules WHERE code = ?", (code,))
    module = add_column_names(cursor.fetchone())
    
    if module is None:
        abort(404)
    
    convener_usernames = module["convener_usernames"].split(",")
    conveners = [] if module["conveners"] == "" else [
        {"name": s.strip(), "username": convener_usernames[i]} for i, s in
        enumerate(module["conveners"].split(","))]
    
    classes = [format_class(*class_) for class_ in parse_table(module["classes"], 4)]
    assessments = [format_assessment(*assessment) for assessment in
                   parse_table(module["assessment"], 5)]
    co_requisites = [co_requisite for co_requisite in parse_table(module["co_requisites"], 2)]
    crawl_time = datetime.fromtimestamp(int(module["crawl_time"]), timezone.utc).strftime(
        "%d/%m/%Y")
    
    # public_token = sha256(bytes(request.remote_addr, "utf-8")).hexdigest()
    
    return render_template("module.html.jinja",
                           module=module,
                           conveners=conveners,
                           co_requisites=co_requisites,
                           classes=classes,
                           assessments=assessments,
                           crawl_time=crawl_time,
                           # public_token=public_token,
                           # public_token_short=public_token[0:10],
                           feature_flags=FEATURE_FLAGS)
