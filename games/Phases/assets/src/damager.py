# damager.py
class Damager:
    """Mixin class for enemies and bullets that cause game over."""
    def __init__(self):
        self.damage = 1