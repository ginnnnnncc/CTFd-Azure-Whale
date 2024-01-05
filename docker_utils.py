from .db_utils import DBUtils
from az.cli import az
import os
import json


class DockerUtils:

    @staticmethod
    def create_container_group(resource_group, container_name, yaml, flag, cpu):
        DBUtils.update_resource_group_used(resource_group, cpu)
        yaml = yaml.replace("#CONTAINER_NAME#", container_name).replace("#FLAG#", flag)
        if not os.path.exists("/tmp/chall_yaml"):
            os.makedirs("/tmp/chall_yaml")
        yaml_path = f"/tmp/chall_yaml/{container_name}.yaml"
        with open(yaml_path, "w") as f:
            f.write(yaml)
            
        exit_code, result_dict, logs = az("container create -g " + resource_group + " -f " + yaml_path)
        print(exit_code, json.dumps(result_dict), logs)
        if exit_code == 0:
            DBUtils.update_container_ip(container_name, result_dict["properties"]["ipAddress"]["ip"])
            DBUtils.update_container_status(container_name, "Running")
        else:
            with open("error.log", "a") as f:
                f.write(logs)

    @staticmethod
    def delete_container_group(resource_group, container_name, cpu):
        DBUtils.update_resource_group_used(resource_group, -cpu)
        DBUtils.update_container_status(container_name, "Deleted")
        exit_code, result_dict, logs = az(f"container delete -g {resource_group} -n {container_name} -y")
        if exit_code == 0:
            return True
        else:
            raise Exception(logs)

