from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import tbapy

app = Flask(__name__)
tba = tbapy.TBA("ZF8araneSrIcZkQilOAmdvm7ULbcyOcQrBKfan0Yh3AghfoXuPgBDqxlRZ4Jv2Kv")
year = datetime.now().strftime("%Y")


def sort_matches(matches):
    return sorted(matches, key=lambda k: k["predicted_time"])


def get_next_and_previous_match(matches):
    previous_match = ""
    next_predicted_match = ""
    for match in matches:
        if match["actual_time"]:
            previous_match = match["key"]
        else:
            next_predicted_match = match["key"]
            break
    return previous_match, next_predicted_match


@app.route('/')
def home():
    return render_template("main.html")


@app.route("/<int:team_number>/")
def team_select(team_number):
    team_object = tba.team(team_number)
    if "Errors" in team_object:
        return render_template("team_missing.html")
    return render_template("event_select.html", events=tba.team_events(team=team_number, year=year), team=team_number)


@app.route("/<int:team_number>/event/<string:event>/")
def view_team(team_number, event):
    matches = tba.team_matches(team_number, event=event, year=year, simple=True)
    if not matches:
        return render_template("no_matches_seeded.html", team=team_number)
    event_object = tba.event(event=event)
    team_object = tba.team(team_number)
    return render_template("viewer.html", team=team_object, event=event_object)


@app.route("/<int:team_number>/event/<string:event>/next_previous_match/")
def next_match_info(team_number, event):
    matches = sort_matches(tba.team_matches(team_number, event=event, year=year, simple=True))
    previous_key, next_key = get_next_and_previous_match(matches)
    previous_match = tba.match(key=previous_key)
    next_match = tba.match(key=next_key)
    return jsonify([previous_match, next_match])


@app.route("/<int:team_number>/event/<string:event>/match_info/")
def match_info(team_number, event):
    matches = tba.team_matches(team_number, event=event, year=year, simple=True)
    return jsonify(matches)


if __name__ == '__main__':
    app.run()
