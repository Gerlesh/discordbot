import nextcord
from nextcord.ext import commands

class HelpMenu(nextcord.ui.Select):
    def __init__(self, bot:commands.Bot, mapping:dict):
        self.bot = bot
        self.mapping = mapping
        options = [nextcord.SelectOption(
                    label=cog.qualified_name,
                    description = cog.description,
                    default=cog.qualified_name == "General")
                    for cog in mapping.keys()]
        super().__init__(min_values=1, max_values=1, options=options)

    async def callback(self, interaction:nextcord.Interaction):
        embed = nextcord.Embed(title="Commands")
        cog = self.bot.get_cog(self.values[0])
        embed.add_field(name="**__" + cog.qualified_name + "__**",
                        value=cog.description,
                        inline=False)

        for command in sorted(self.mapping[cog], key=lambda x: x.name):
            embed.add_field(name=command.name, value=command.help.split("\n")[0])

        for option in self.options:
            if option.default and option.label != self.values[0]:
                option.default = False
            if option.label == self.values[0] and not option.default:
                option.default = True

        await interaction.edit(embed=embed,view=self.view)
