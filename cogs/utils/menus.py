import nextcord
from nextcord.ext import commands

class HelpMenu(nextcord.ui.Select):
    def __init__(self, mapping:dict):
        self.mapping = mapping
        options = [nextcord.SelectOption(
                    label=cog.qualified_name if hasattr(cog, 'qualified_name') else str(cog),
                    description = cog.description if (hasattr(cog, 'description') and cog.description) else "Miscellaneous commands",
                    default=not hasattr(cog, 'qualified_name'))
                    for cog in mapping.keys()]
        super().__init__(placeholder=[cog for cog in mapping if isinstance(cog,str)][0], min_values=1, max_values=1, options=options)

    async def callback(self, interaction:nextcord.Interaction):
        def find_cog(name):
            for cog in self.mapping.keys():
                if hasattr(cog, 'qualified_name'):
                    if cog.qualified_name == name:
                        return cog
                elif str(cog) == name:
                    return cog

        embed = nextcord.Embed(title="Commands")
        cog = find_cog(self.values[0])
        embed.add_field(name="**__" + self.values[0] + "__**",
                        value=cog.description if (
                                hasattr(cog, 'description') and cog.description) else "Miscellaneous commands",
                        inline=False)

        for command in self.mapping[cog]:
            embed.add_field(name=command.name, value=command.help.split("\n")[0])

        for option in self.options:
            if option.default and option.label != self.values[0]:
                option.default = False
            if option.label == self.values[0] and not option.default:
                option.default = True

        await interaction.edit(embed=embed,view=self.view)