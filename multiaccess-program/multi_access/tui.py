from getpass import getpass
from logging import getLogger

logger = getLogger("makeradmin")


class Tui(object):
    """ A tui abstractions, let's see how this works. """

    @staticmethod
    def promt__login():
        print("login to maker admin")
        username = input("    username (email): ")
        password = getpass("    password: ")
        return username, password

    @staticmethod
    def prompt__update_db(heading=None, lines=None):
        """ Propmt to the user and give the choise of stopping (raiss SystemExit) or continuing. """
        print()
        print(heading)
        for line in lines:
            print("    ", line)
        print()
        try:
            valid_input = False
            while not valid_input:
                user_command = input("'go' to perform all, 'exit' to abort: ").strip().lower()
                if user_command == 'go':
                    valid_input = True
                elif user_command == 'exit':
                    raise KeyboardInterrupt()
        except KeyboardInterrupt:
            raise SystemExit()

    @staticmethod
    def prompt__run_again():
        try:
            print()
            if input("press enter to run again again, ctrl-c or 'exit' to exit: ").strip() == 'exit':
                raise KeyboardInterrupt()
        except KeyboardInterrupt:
            raise SystemExit()

    @staticmethod
    def info__progress(msg):
        logger.info(msg)

    @staticmethod
    def fatal__error(msg):
        logger.error(msg)
        raise SystemExit()

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
    