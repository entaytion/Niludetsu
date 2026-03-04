from __future__ import annotations

import discord
from Niludetsu.tools.Embed import Colors


class InfoCard:
    """Universal Components V2 info card builder.

    Usage::

        card = InfoCard(colour=0xAEDEAD)
        card.thumbnail_url = "https://..."
        card.header = "**Title**\n- description"
        card.sections = ["section 1 text", "section 2 text"]
        card.footer = "-# small footer"
        
        # New V2 Features!
        card.add_item(discord.ui.ActionRow(...))
        card.add_media_gallery(["https://...", "https://..."])
        card.add_file("https://...")
        
        await ctx.send(view=card.build())
    """

    def __init__(self, *, colour: int = Colors.PRIMARY):
        self.colour = colour
        self.header: str | None = None
        self.thumbnail_url: str | None = None
        self.sections: list[str] = []
        self.footer: str | None = None
        
        # New dynamic components list for V2
        self.components: list[discord.ui.Item] = []

    def add_item(self, item: discord.ui.Item) -> InfoCard:
        """Add a raw discord.ui V2 component (like ActionRow, TextDisplay, Section, etc)."""
        self.components.append(item)
        return self

    def add_media_gallery(self, urls: list[str]) -> InfoCard:
        """Helper to add a MediaGallery containing multiple images."""
        gallery = discord.ui.MediaGallery()
        for url in urls:
            gallery.add_item(media=url)
        self.components.append(gallery)
        return self
        
    def add_file(self, media: str | discord.File, spoiler: bool = False) -> InfoCard:
        """Helper to append a File component."""
        self.components.append(discord.ui.File(media=media, spoiler=spoiler))
        return self
        
    def add_separator(self, visible: bool = True) -> InfoCard:
        """Helper to append a visible or invisible Separator."""
        self.components.append(discord.ui.Separator(visible=visible))
        return self

    def build(self) -> discord.ui.LayoutView:
        children: list[discord.ui.Item] = []

        if self.header:
            if self.thumbnail_url:
                children.append(discord.ui.Section(
                    self.header,
                    accessory=discord.ui.Thumbnail(self.thumbnail_url),
                ))
            else:
                children.append(discord.ui.TextDisplay(self.header))

        for text in self.sections:
            children.append(discord.ui.Separator())
            children.append(discord.ui.TextDisplay(text))
            
        # Append all dynamically added V2 components
        children.extend(self.components)

        if self.footer:
            children.append(discord.ui.Separator())
            children.append(discord.ui.TextDisplay(self.footer))

        container = discord.ui.Container(
            *children,
            accent_colour=discord.Colour(self.colour),
        )
        view = discord.ui.LayoutView(timeout=None)
        view.add_item(container)
        return view
