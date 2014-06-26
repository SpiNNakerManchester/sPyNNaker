def enum1(*enums):
    pairs = list(enumerate(enums, start=1))
    return type('Enum', (),
                dict(map(lambda (v, k): (k, v), pairs))
                )


def enum0(*enums):
    pairs = list(enumerate(enums, start=0))
    return type('Enum', (),
                dict(map(lambda (v, k): (k, v), pairs))
                )

edges = enum0('EAST', 'NORTH_EAST', 'NORTH', 'WEST', 'SOUTH_WEST', 'SOUTH')
