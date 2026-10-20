from .buildings import block_house, courtyard_house

FACADE = "col_facade"
FACADE_BRICK = "col_facade_brick"


def court(width, depth, court_width, court_depth, height, material, tone):
    builder = courtyard_house(width, depth, court_width, court_depth, height, material, court_material="plaster_grey")
    return builder.paint(material, tone)


def block(width, depth, height, material, tone, shops):
    builder = block_house(width, depth, height, material, shops=shops, windows=0)
    return builder.paint(material, tone)


INSULAE = {
    "insula_court_a": lambda: court(30.0, 24.0, 11.0, 8.0, 15.0, FACADE, (0.93, 0.76, 0.56)),
    "insula_court_b": lambda: court(27.0, 22.0, 9.0, 7.0, 18.0, FACADE_BRICK, (1.0, 1.0, 1.0)),
    "insula_block_a": lambda: block(20.0, 12.0, 12.0, FACADE, (0.96, 0.82, 0.74), 5),
    "insula_block_b": lambda: block(24.0, 13.0, 16.0, FACADE_BRICK, (0.95, 0.95, 0.95), 6),
    "domus_low": lambda: block(16.0, 11.0, 7.0, FACADE, (0.99, 0.93, 0.8), 2),
}
