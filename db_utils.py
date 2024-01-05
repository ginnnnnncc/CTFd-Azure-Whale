import datetime
import uuid

from .models import WhaleConfig, WhaleContainer, ResourceGroup

from CTFd.models import (
    db
)


class DBUtils:
    @staticmethod
    def get_all_configs():
        configs = WhaleConfig.query.all()
        result = {}

        for c in configs:
            result[str(c.key)] = str(c.value)

        return result

    @staticmethod
    def save_all_configs(configs):
        for c in configs:
            q = db.session.query(WhaleConfig)
            q = q.filter(WhaleConfig.key == c[0])
            record = q.one_or_none()

            if record:
                record.value = c[1]
                db.session.commit()
            else:
                config = WhaleConfig(key=c[0], value=c[1])
                db.session.add(config)
                db.session.commit()
        db.session.close()

    @staticmethod
    def create_new_container(user_id, challenge_id, container_name, resource_group_name, flag, cpu):
        container = WhaleContainer(user_id=user_id, challenge_id=challenge_id,flag=flag, cpu=cpu,
                                   container_name=container_name, resource_group_name=resource_group_name)
        db.session.add(container)
        db.session.commit()
        db.session.close()

    @staticmethod
    def get_current_containers(user_id):
        q = db.session.query(WhaleContainer).filter(WhaleContainer.visible == True)
        q = q.filter(WhaleContainer.user_id == user_id)
        records = q.all()
        if len(records) == 0:
            return None

        return records[0]

    @staticmethod
    def remove_current_container(user_id):
        q = db.session.query(WhaleContainer).filter(WhaleContainer.visible == True)
        r = q.filter(WhaleContainer.user_id == user_id).first()
        if r:
            r.visible = False
            r.status = "Deleted"

        db.session.commit()
        db.session.close()

    @staticmethod
    def renew_current_container(user_id, challenge_id):
        q = db.session.query(WhaleContainer).filter(WhaleContainer.visible == True)
        q = q.filter(WhaleContainer.user_id == user_id)
        q = q.filter(WhaleContainer.challenge_id == challenge_id)
        records = q.all()
        if len(records) == 0:
            return

        configs = DBUtils.get_all_configs()
        timeout = int(configs.get("docker_timeout", "3600"))

        r = records[0]
        r.start_time = r.start_time + datetime.timedelta(seconds=timeout)

        if r.start_time > datetime.datetime.now():
            r.start_time = datetime.datetime.now()

        r.renew_count += 1
        db.session.commit()
        db.session.close()

    @staticmethod
    def get_all_expired_container():
        configs = DBUtils.get_all_configs()
        timeout = int(configs.get("docker_timeout", "3600"))

        q = db.session.query(WhaleContainer).filter(WhaleContainer.visible == True)
        q = q.filter(WhaleContainer.start_time < datetime.datetime.now() - datetime.timedelta(seconds=timeout))
        return q.all()

    @staticmethod
    def get_all_container():
        q = db.session.query(WhaleContainer)
        return q.all()

    @staticmethod
    def get_all_container_page(page_start, page_end):
        q = db.session.query(WhaleContainer)
        q = q.order_by(WhaleContainer.start_time.desc())
        q = q.slice(page_start, page_end)
        return q.all()

    @staticmethod
    def get_all_alive_container_count():
        configs = DBUtils.get_all_configs()
        timeout = int(configs.get("docker_timeout", "3600"))
        
        q = db.session.query(WhaleContainer).filter(WhaleContainer.visible == True)
        q = q.filter(WhaleContainer.start_time >= datetime.datetime.now() - datetime.timedelta(seconds=timeout))
        return q.count()
    
    @staticmethod
    def get_all_reource_group():
        q = db.session.query(ResourceGroup)
        return q.all()
    
    @staticmethod
    def get_available_resource_group(request_cpu):
        q = db.session.query(ResourceGroup).filter(ResourceGroup.used <= 6 - request_cpu).order_by(ResourceGroup.priority.asc())
        return q.first()

    @staticmethod
    def update_resource_group_used(name, variation):
        record = db.session.query(ResourceGroup).filter(ResourceGroup.name == name).first()

        if record:
            record.used += variation
            db.session.commit()
        else:
            raise Exception("Resource group not found")

        db.session.close()
        return True
    
    @staticmethod
    def update_container_status(container_name, status):
        record = None
        if status == "Running":
            record = db.session.query(WhaleContainer).filter(WhaleContainer.visible == True, WhaleContainer.container_name == container_name).first()  
        elif status == "Deleted":
            record = db.session.query(WhaleContainer).filter(WhaleContainer.status != "Deleted", WhaleContainer.container_name == container_name).first()
            
        if record:
            record.status = status
            db.session.commit()
        else:
            raise Exception("Container not found")
        
        db.session.close()
        return True
    
    @staticmethod
    def update_container_ip(container_name, ip):
        record = db.session.query(WhaleContainer).filter(WhaleContainer.visible == True, WhaleContainer.container_name == container_name).first()  
        if record:
            record.ip = ip
            db.session.commit()
        else:
            raise Exception("Container not found")
        
        db.session.close()
        return True