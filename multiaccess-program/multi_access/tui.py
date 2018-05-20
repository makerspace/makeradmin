from logging import getLogger

logger = getLogger("makeradmin")

class Tui(object):
    """ A tui abstractions, let's see how this works. """

    def login(self, gateway):
        username = input("Username (email): ")
        password = input("Password: ")
        gateway.login(username, password)

    @staticmethod
    def info__progress(msg):
        logger.info(msg)

    @staticmethod
    def fatal__error(msg):
        logger.error(msg)
        raise SystemExit()
        # TODO Is it ugly to have control flow in the tui code like this, or is it nice because it makes it harder to
        # introduce bugs where the program is not aborted on fatal errors (because this is easier to test)?

    @staticmethod
    def fatal__problem_members(problem_members):
        logger.error('the following members have unexpected fields in maker admin, please fix them and run again')
        for pm in problem_members:
            logger.error(f'   {pm.user.name.strip()}: {", ".join(pm.problems)}')
        raise SystemExit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    