from flask import Flask, render_template, jsonify, request, make_response
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
    if not previous_match:
        return None, next_predicted_match
    if not next_predicted_match:
        return previous_match, None
    return previous_match, next_predicted_match


def check_next_match(matches):
    for match in matches:
        if not match["actual_time"]:
            return True
    return False


def get_team_alliance(match, team_number):
    for team in match["alliances"]["blue"]["team_keys"]:
        if f"frc{team_number}" == team:
            return "blue"
    for team in match["alliances"]["red"]["team_keys"]:
        if f"frc{team_number}" == team:
            return "blue"
    return None


@app.route("/")
def home():
    if not request.cookies.get("credits"):
        resp = make_response(render_template("main.html", credit_mode="On"))
        resp.set_cookie("credits", "On")
        return resp
    return render_template("main.html", credit_mode=request.cookies.get("credits"))


@app.route("/credits/<string:mode>")
def set_credits(mode):
    resp = make_response("")
    resp.set_cookie("credits", mode)
    return resp


@app.route("/<int:team_number>/")
def team_select(team_number):
    team_object = tba.team(team_number)
    if "Errors" in team_object:
        return render_template("errors/team_missing.html")
    return render_template("event_select.html", events=tba.team_events(team=team_number, year=year), team=team_number)


@app.route("/<int:team_number>/event/<string:event>/")
def view_team(team_number, event):
    matches = tba.team_matches(team_number, event=event, year=year, simple=True)
    if not matches:
        return render_template("errors/no_matches_seeded.html", team=team_number)
    if not check_next_match(matches):
        return render_template("errors/current_no_matches.html", team=team_number)
    event_object = tba.event(event=event)
    team_object = tba.team(team_number)
    return render_template("viewer.html", team=team_object, event=event_object)


@app.route("/<int:team_number>/event/<string:event>/next_previous_match/")
def next_match_info(team_number, event):
    matches = sort_matches(tba.team_matches(team_number, event=event, year=year, simple=True))
    previous_key, next_key = get_next_and_previous_match(matches)
    standings = tba.team_status(team_number, event)
    if previous_key:
        previous_match = tba.match(key=previous_key)
        previous_match["our_team_alliance"] = get_team_alliance(previous_match, team_number)
    if next_key:
        next_match = tba.match(key=next_key)
        next_match["delay"] = next_match["predicted_time"] - datetime.now().timestamp()
        next_match["our_team_alliance"] = get_team_alliance(next_match, team_number)
    if previous_key and next_key:
        return jsonify([previous_match, next_match, standings])
    elif previous_key:
        return jsonify([previous_match, None, standings])
    elif next_key:
        return jsonify([None, next_match, standings])
    else:
        return [None, None, standings]

@app.route("/<int:team_number>/event/<string:event>/match_info/")
def match_info(team_number, event):
    matches = tba.team_matches(team_number, event=event, year=year, simple=True)
    return jsonify(matches)


@app.route("/demo")
def demo():
    team_number = 1157
    event = "2019code"
    event_object = tba.event(event=event)
    team_object = tba.team(team_number)
    return render_template("viewer.html", team=team_object, event=event_object)


if __name__ == '__main__':
    app.run()
