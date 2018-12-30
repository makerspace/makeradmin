from logging import INFO
from os.path import abspath, join, basename, exists

from rocky.config import Config, Dict, Env

from service.logging import logger


class DockerEnvFile(Dict):
    """ Config reader to read from docker .env file. """
    
    # TODO BM use python-dotenv instead
    
    def __init__(self, filename, name=None, **kwargs):
        if not exists(filename):
            logger.info(f"docker .env file {filename} does not exist, skipping")
            env = {}
        else:
            with open(filename) as f:
                env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}
            
        super().__init__(env, name=name or filename, **kwargs)


default = Dict(name="default", src=dict(
    MYSQL_HOST='localhost',
    MYSQL_PORT=3306,
    MYSQL_USER='makeradmin',
    MYSQL_DB='makeradmin',
    MEMBERSHIP_URL='http://membership',
    SHOP_URL='http://backend',
    MEMBER_URL='http://backend',
    MESSAGES_URL='http://messages',
    EMAIL_DISPATCHER_URL='http://email-dispatcher',
    MULTIACCESS_SYNC_URL='http://multiaccesssync',
))
env = Env()
docker_env = DockerEnvFile(abspath(join(basename(__file__), '../../../.env')))

config = Config(env, docker_env, default, log_level=INFO)


def get_mysql_config():
    host = config.get('MYSQL_HOST')
    port = int(config.get('MYSQL_PORT'))
    db = config.get('MYSQL_DB')
    user = config.get('MYSQL_USER')
    pwd = config.get('MYSQL_PASS', log_value=False)
    if not pwd: raise Exception("config MYSQL_PASS is required")
    
    return dict(host=host, port=port, db=db, user=user, pwd=pwd)
