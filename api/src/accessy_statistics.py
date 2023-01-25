from multiaccessy.accessy import accessy_session


doors = accessy_session.get_all_doors()
for door in doors:
    print(f"Door: {door}", end="")
    accesses = accessy_session.get_all_accesses(door)
    print("    Accesses: ", end="")
    print(accesses)
