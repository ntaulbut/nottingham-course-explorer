import string
from datetime import datetime, timezone

from flask import abort, render_template, url_for, redirect
from num2words import num2words

from config import FEATURE_FLAGS
from tools import add_column_names, get_db, parse_table, add_column_names_list


def format_class(class_type: str, weeks: str, per_week_str: str, duration: str) -> str:
    duration = (duration
                .replace("and ", "")
                .replace("hours", "hour")
                .replace("minutes", "minute")
                .replace(" ", "-")) + " " if duration != "" else ""
    if weeks == "1 week":
        return f"One {duration}{class_type.lower()}"
    per_week = int(per_week_str.split(" ")[0]) if per_week_str else 1
    return f"{string.capwords(num2words(per_week))} {duration}{class_type.lower()}{'s' if per_week > 1 else ''} per week for {weeks}"


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

    cursor.execute("SELECT username, salutation, forename, surname FROM staff "
                   "JOIN convenes ON username = staff_username WHERE module_code = ?", (code,))
    known_conveners = add_column_names_list(cursor.fetchall())

    cursor.execute("SELECT name FROM unknown_conveners WHERE module_code = ?", (code,))
    unknown_conveners = add_column_names_list(cursor.fetchall())

    classes = [format_class(*class_) for class_ in parse_table(module["classes"], 4)]
    assessments = [format_assessment(*assessment) for assessment in parse_table(module["assessment"], 5)]
    co_requisites = [co_requisite for co_requisite in parse_table(module["co_requisites"], 2)]
    prerequisites = [prerequisite for prerequisite in parse_table(module["prerequisites"], 2)]

    crawl_time = datetime.fromtimestamp(int(module["crawl_time"]), timezone.utc).strftime("%d/%m/%Y")

    # public_token = sha256(bytes(request.remote_addr, "utf-8")).hexdigest()

    return render_template("module.html.jinja",
                           module=module,
                           known_conveners=known_conveners,
                           unknown_conveners=unknown_conveners,
                           co_requisites=co_requisites,
                           prerequisites=prerequisites,
                           classes=classes,
                           assessments=assessments,
                           crawl_time=crawl_time,
                           # public_token=public_token,
                           # public_token_short=public_token[0:10],
                           feature_flags=FEATURE_FLAGS)


def find_module(code: str):
    cursor = get_db().cursor()
    cursor.execute("SELECT code FROM modules WHERE code = ?", (code,))
    module = add_column_names(cursor.fetchone())
    if module is None:
        abort(404)
    return url_for("module_page", code=module["code"])


def random_module():
    cursor = get_db().cursor()
    cursor.execute("SELECT code FROM modules ORDER BY RANDOM() LIMIT 1")
    module = add_column_names(cursor.fetchone())
    if module is None:
        abort(404)
    return redirect(url_for("module_page", code=module["code"]))
