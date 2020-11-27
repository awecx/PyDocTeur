import json
import os
from functools import partial

from dotenv import load_dotenv
from flask import Flask
from flask import request

from pydocteur.utils.get_pr import get_pull_request
from pydocteur.utils.pr_status import are_labels_set
from pydocteur.utils.pr_status import get_checks_statuses_conclusions
from pydocteur.utils.pr_status import is_pr_approved
from pydocteur.utils.state_actions import comment_pr


load_dotenv()

REQUIRED_ENV_VARS = ["GH_TOKEN", "REPOSITORY_NAME"]

for var in REQUIRED_ENV_VARS:
    if var not in os.environ:
        raise EnvironmentError(f"Missing {var} in environment")

application = Flask(__name__)


def state_name(**kwargs):
    return "_".join(key for key, value in kwargs.items() if value)


@application.route("/", methods=["POST"])
def process_incoming_payload():
    payload = json.loads(request.data)
    if payload["sender"]["login"] == "PyDocTeur":
        return "OK", 200
    pr = get_pull_request(payload)
    if not pr:
        return "OK", 200

    is_automerge, is_donotmerge = are_labels_set(pr)
    is_ci_success = get_checks_statuses_conclusions(pr)
    is_approved = is_pr_approved(pr)
    state = state_name(automerge=is_automerge, approved=is_approved, testok=is_ci_success, donotmerge=is_donotmerge)
    my_comments = [comment.body for comment in pr.get_issue_comments() if comment.user.login == "PyDocTeur"]
    if my_comments and state in my_comments[-1]:
        print("State has not changed, ignoring event.")
        return
    big_dict = {
        "automerge_approved": comment_pr
        # ...
    }
    big_dict.get(state, comment_pr)(state=state, pr=pr)
    return "OK", 200
