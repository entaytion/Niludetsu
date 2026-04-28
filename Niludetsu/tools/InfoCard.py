from Niludetsu.tools.Embed import Embed, Colors

class InfoCard:
    @staticmethod
    def create(*args, **kwargs) -> Embed:
        return Embed.info(*args, **kwargs)
