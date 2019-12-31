from dataclasses import dataclass

import arrow
from flask import render_template, flash, redirect, url_for, abort
from flask_login import login_required, current_user

from app.dashboard.base import dashboard_bp
from app.extensions import db
from app.models import GenEmail, ForwardEmailLog, ForwardEmail

LIMIT = 3


@dataclass
class AliasLog:
    website_email: str
    website_from: str
    alias: str
    when: arrow.Arrow
    is_reply: bool
    blocked: bool


@dashboard_bp.route("/alias_log/<alias>", methods=["GET"], defaults={'page_id': 0})
@dashboard_bp.route("/alias_log/<alias>/<int:page_id>")
@login_required
def alias_log(alias, page_id):
    gen_email = GenEmail.get_by(email=alias)

    # sanity check
    if not gen_email:
        flash("You do not have access to this page", "warning")
        return redirect(url_for("dashboard.index"))

    if gen_email.user_id != current_user.id:
        flash("You do not have access to this page", "warning")
        return redirect(url_for("dashboard.index"))

    logs = get_alias_log(gen_email, page_id)
    last_page = len(logs) < LIMIT  # lightweight pagination without counting all objects

    return render_template(
        "dashboard/alias_log.html", **locals()
    )


def get_alias_log(gen_email: GenEmail, page_id=0):
    logs: [AliasLog] = []

    q = (
        db.session.query(ForwardEmail, ForwardEmailLog)
            .filter(ForwardEmail.id == ForwardEmailLog.forward_id)
            .filter(ForwardEmail.gen_email_id == gen_email.id)
            .limit(LIMIT)
            .offset(page_id * LIMIT)
    )

    for fe, fel in q:
        al = AliasLog(
            website_email=fe.website_email,
            website_from=fe.website_from,
            alias=gen_email.email,
            when=fel.created_at,
            is_reply=fel.is_reply,
            blocked=fel.blocked,
        )
        logs.append(al)

    logs = sorted(logs, key=lambda l: l.when, reverse=True)

    return logs
