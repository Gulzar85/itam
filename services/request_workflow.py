from requests.models import Request


ALLOWED_STATUS_TRANSITIONS = {
    'PENDING': {'MANAGER_APPROVED', 'REJECTED'},
    'MANAGER_APPROVED': {'IT_RECEIVED', 'COMPLETED', 'REJECTED'},
    'IT_RECEIVED': {'IN_PROGRESS', 'COMPLETED', 'REJECTED'},
    'IN_PROGRESS': {'COMPLETED', 'REJECTED'},
    'READY': {'COMPLETED', 'REJECTED'},
}


def get_valid_statuses() -> set[str]:
    return {choice[0] for choice in Request.STATUS_CHOICES}


def is_valid_transition(current_status: str, new_status: str) -> bool:
    if current_status == new_status:
        return False
    return new_status in ALLOWED_STATUS_TRANSITIONS.get(current_status, set())


def is_it_admin(user) -> bool:
    return bool(user and getattr(user, 'role', None) == 'IT_ADMIN')


def can_actor_transition(actor, request_obj: Request, new_status: str) -> bool:
    current_status = request_obj.status
    if not is_valid_transition(current_status, new_status):
        return False
    if actor is None:
        return False
    if is_it_admin(actor):
        return True

    is_direct_manager = request_obj.user.manager_id == actor.id
    if not is_direct_manager:
        return False

    return current_status == 'PENDING' and new_status in {'MANAGER_APPROVED', 'REJECTED'}
