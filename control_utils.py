import time

from CTFd.models import Challenges, Users
from .db_utils import DBUtils
from .docker_utils import DockerUtils
from sqlalchemy.sql import and_
from flask import session

class ControlUtil:
    @staticmethod
    def add_container(user_id, challenge_id, resource_group_name, container_basename, yaml, flag, cpu):
        container_name = f"{container_basename}-{user_id}"
        DBUtils.create_new_container(user_id, challenge_id, container_name, resource_group_name, flag, cpu)
        DockerUtils.create_container_group(resource_group_name, container_name, yaml, flag, cpu)

    @staticmethod
    def remove_container(user_id):
        container = ControlUtil.get_container(user_id)
        if container is None:
            return
        docker_result = DockerUtils.delete_container_group(container.resource_group_name, container.container_name, container.cpu)
        if docker_result:
            DBUtils.remove_current_container(user_id)

        return docker_result

    @staticmethod
    def get_container(user_id):
        return DBUtils.get_current_containers(user_id=user_id)

    @staticmethod
    def renew_container(user_id, challenge_id):
        DBUtils.renew_current_container(user_id=user_id, challenge_id=challenge_id)

    @staticmethod
    def check_challenge(challenge_id, user_id):
        user = Users.query.filter_by(id=user_id).first()

        if user.type == "admin":
            Challenges.query.filter(
                Challenges.id == challenge_id
            ).first_or_404()
        else:
            Challenges.query.filter(
                Challenges.id == challenge_id,
                and_(Challenges.state != "hidden", Challenges.state != "locked"),
            ).first_or_404()

    @staticmethod
    def frequency_limit():
        if "limit" not in session:
            session["limit"] = int(time.time())
            return False

        if int(time.time()) - session["limit"] < 60:
            return True

        session["limit"] = int(time.time())
        return False
