from functools import wraps
from typing import Iterable, Union

from flask import render_template, session

from models import User, db


RoleSpec = Union[str, Iterable[str]]


def _normalize_roles(role_spec: RoleSpec) -> set:
    if isinstance(role_spec, str):
        return {role_spec}
    return {r for r in role_spec if isinstance(r, str)}


def role_required(role_spec: RoleSpec):
    required_roles = _normalize_roles(role_spec)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return render_template('403.html'), 403

            user = db.session.get(User, user_id)
            if user is None or user.role not in required_roles or not user.active:
                return render_template('403.html'), 403

            return view_func(*args, **kwargs)

        return wrapped

    return decorator


admin_required = role_required('admin')


counselor_required = role_required('counselor')


student_required = role_required('student')
