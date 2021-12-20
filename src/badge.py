import math
import asyncio

import discord
from discord.ext import commands
from discord.commands import slash_command, Option, permissions

from database import DatabasePersonality, DatabaseDeck
import utils


class Badge(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @slash_command(description='Add a badge.',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def add_badge(self, ctx, name: str):
        added = DatabaseDeck.get().add_badge(ctx.interaction.guild.id, name)
        if not added:
            await ctx.respond('Error : the badge probably already exists.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
        else:
            await ctx.respond(f'New badge {name} added!')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u2705")

    @slash_command(description='Remove a badge.',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def remove_badge(self, ctx, name: Option(str, 'Pick a badge name', autocomplete=utils.badges_name_searcher)):
        id_badge = DatabaseDeck.get().get_id_badge(ctx.interaction.guild.id, name)
        if not id_badge:
            await ctx.respond(f'Badge {name} not found.')
            return

        DatabaseDeck.get().remove_badge(id_badge)
        await ctx.respond(f'Badge {name} removed.')
        msg = await ctx.interaction.original_message()
        await msg.add_reaction(u"\u2705")

    @slash_command(description='Add a personality to a badge',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def add_perso_to_badge(self, ctx,
                                 badge_name: Option(str, 'Pick a badge name', autocomplete=utils.badges_name_searcher),
                                 personality: Option(str, "Pick a name or write yours",
                                                     autocomplete=utils.personalities_name_searcher),
                                 group: Option(str, "Pick a group or write yours",
                                               autocomplete=utils.personalities_group_searcher, required=False,
                                               default=None)):

        id_badge = DatabaseDeck.get().get_id_badge(ctx.interaction.guild.id, badge_name)
        if not id_badge:
            await ctx.respond(f'Badge {badge_name} not found.')
            return

        personality = personality.strip()
        if group:
            group = group.strip()

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(personality, group)
        else:
            id_perso = DatabasePersonality.get().get_perso_id(personality)

        if not id_perso:
            msg = f'I searched everywhere for **{personality}**'
            if group:
                msg += f' in the group *{group}*'
            msg += ' and I couldn\'t find anything.\nPlease check the command.'
            await ctx.respond(msg)
            return

        if id_perso in DatabaseDeck.get().get_perso_in_badge(id_badge):
            await ctx.respond(f'Personnality {personality} is already in {badge_name}.')
            return

        DatabaseDeck.get().add_perso_to_badge(id_badge, id_perso)
        await ctx.respond(f'{personality} added to {badge_name}!')
        msg = await ctx.interaction.original_message()
        await msg.add_reaction(u"\u2705")

    @slash_command(description='Add a personality to a badge',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def remove_perso_from_badge(self, ctx,
                                      badge_name: Option(str, 'Pick a badge name',
                                                         autocomplete=utils.badges_name_searcher),
                                      personality: Option(str, "Pick a name or write yours",
                                                          autocomplete=utils.personalities_name_searcher),
                                      group: Option(str, "Pick a group or write yours",
                                                    autocomplete=utils.personalities_group_searcher, required=False,
                                                    default=None)):

        id_badge = DatabaseDeck.get().get_id_badge(ctx.interaction.guild.id, badge_name)
        if not id_badge:
            await ctx.respond(f'Badge {badge_name} not found.')
            return

        personality = personality.strip()
        if group:
            group = group.strip()

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(personality, group)
        else:
            id_perso = DatabasePersonality.get().get_perso_id(personality)

        if not id_perso:
            msg = f'I searched everywhere for **{personality}**'
            if group:
                msg += f' in the group *{group}*'
            msg += ' and I couldn\'t find anything.\nPlease check the command.'
            await ctx.respond(msg)
            return

        if id_perso not in DatabaseDeck.get().get_perso_in_badge(id_badge):
            await ctx.respond(f'Personnality {personality} is not in {badge_name}.')
            return

        DatabaseDeck.get().remove_perso_from_badge(id_badge, id_perso)
        await ctx.respond(f'{personality} removed from {badge_name}.')
        msg = await ctx.interaction.original_message()
        await msg.add_reaction(u"\u2705")

    @slash_command(description='Show all personalities in this badge',
                   guild_ids=utils.get_authorized_guild_ids())
    async def show_badge(self, ctx,
                         badge_name: Option(str, 'Pick a badge name', autocomplete=utils.badges_name_searcher)):
        id_badge = DatabaseDeck.get().get_id_badge(ctx.interaction.guild.id, badge_name)
        if not id_badge:
            await ctx.respond(f'Badge {badge_name} not found.')
            return

        ids = DatabaseDeck.get().get_perso_in_badge(id_badge)

        persos_text = []
        personalities = DatabasePersonality.get().get_multiple_perso_information(ids)
        if personalities:
            for perso in personalities:
                id_owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, perso['id'])
                owner_txt = ''
                if id_owner:
                    owner = ctx.guild.get_member(id_owner)
                    if owner:
                        owner_txt = f' - {owner.name if not owner.nick else owner.nick}'
                persos_text.append(f'**{perso["name"]}** *{perso["group"]}* {owner_txt}')

        persos_text.sort()

        current_page = 1
        nb_per_page = 20
        max_page = math.ceil(len(persos_text) / float(nb_per_page))

        title = f'Badge {badge_name}'
        embed = discord.Embed(title=title,
                              description='\n'.join([perso for perso in persos_text[(
                                                                                                current_page - 1) * nb_per_page:current_page * nb_per_page]]))
        embed.set_footer(text=f'{current_page} \\ {max_page}')
        await ctx.respond(embed=embed)
        msg = await ctx.interaction.original_message()

        if max_page > 1:
            # Page handler
            left_emoji = '\U00002B05'
            right_emoji = '\U000027A1'
            await msg.add_reaction(left_emoji)
            await msg.add_reaction(right_emoji)

            def check(reaction, user):
                return user != self.bot.user and (
                        str(reaction.emoji) == left_emoji or str(reaction.emoji) == right_emoji) \
                       and reaction.message.id == msg.id

            timeout = False

            while not timeout:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reaction(left_emoji)
                    await msg.clear_reaction(right_emoji)
                    timeout = True
                else:
                    old_page = current_page
                    if reaction.emoji == left_emoji:
                        current_page = current_page - 1 if current_page > 1 else max_page

                    if reaction.emoji == right_emoji:
                        current_page = current_page + 1 if current_page < max_page else 1

                    await msg.remove_reaction(reaction.emoji, user)

                    # Refresh embed message with the new text
                    if old_page != current_page:
                        embed = discord.Embed(title=title,
                                              description='\n'.join([perso for perso in persos_text[(
                                                                                                                current_page - 1) * nb_per_page:current_page * nb_per_page]]))
                        embed.set_footer(text=f'{current_page} \\ {max_page}')
                        await msg.edit(embed=embed)

    @slash_command(description='Show all personalities in this badge',
                   guild_ids=utils.get_authorized_guild_ids())
    async def badges_progression(self, ctx, member: Option(discord.Member, required=False, default=None)):
        owner = member or ctx.author
        ids_deck = DatabaseDeck.get().get_user_deck(ctx.guild.id, owner.id)
        badges = DatabaseDeck.get().get_all_badges_with_perso(ctx.guild.id)

        badges_text = []
        if badges:
            for badge_name in badges:
                count = sum([id_perso in ids_deck for id_perso in badges[badge_name]])
                nb_perso = len(badges[badge_name])
                if count == nb_perso:
                    badges_text.append(f'**{badge_name} {count}/{nb_perso} - Finished**')
                else:
                    badges_text.append(f'{badge_name} {count}/{nb_perso}')

        badges_text.sort()

        current_page = 1
        nb_per_page = 20
        max_page = math.ceil(len(badges_text) / float(nb_per_page))

        title = f'Badges progression of {owner.name if not owner.nick else owner.nick}'
        embed = discord.Embed(title=title,
                              description='\n'.join([badge for badge in badges_text[(
                                                                                                current_page - 1) * nb_per_page:current_page * nb_per_page]]))
        embed.set_footer(text=f'{current_page} \\ {max_page}')
        await ctx.respond(embed=embed)
        msg = await ctx.interaction.original_message()

        if max_page > 1:
            # Page handler
            left_emoji = '\U00002B05'
            right_emoji = '\U000027A1'
            await msg.add_reaction(left_emoji)
            await msg.add_reaction(right_emoji)

            def check(reaction, user):
                return user != self.bot.user and (
                        str(reaction.emoji) == left_emoji or str(reaction.emoji) == right_emoji) \
                       and reaction.message.id == msg.id

            timeout = False

            while not timeout:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reaction(left_emoji)
                    await msg.clear_reaction(right_emoji)
                    timeout = True
                else:
                    old_page = current_page
                    if reaction.emoji == left_emoji:
                        current_page = current_page - 1 if current_page > 1 else max_page

                    if reaction.emoji == right_emoji:
                        current_page = current_page + 1 if current_page < max_page else 1

                    await msg.remove_reaction(reaction.emoji, user)

                    # Refresh embed message with the new text
                    if old_page != current_page:
                        embed = discord.Embed(title=title,
                                              description='\n'.join([perso for perso in persos_text[(
                                                                                                            current_page - 1) * nb_per_page:current_page * nb_per_page]]))
                        embed.set_footer(text=f'{current_page} \\ {max_page}')
                        await msg.edit(embed=embed)

    @slash_command(description='Show all badges',
                   guild_ids=utils.get_authorized_guild_ids())
    async def list_badges(self, ctx):
        badges = DatabaseDeck.get().get_all_badges(ctx.interaction.guild.id)

        badges_text = []
        if badges:
            badges_text = [badge['name'] for badge in badges]

        badges_text.sort()

        current_page = 1
        nb_per_page = 20
        max_page = math.ceil(len(badges_text) / float(nb_per_page))

        title = f'Badges'
        embed = discord.Embed(title=title,
                              description='\n'.join([badge for badge in badges_text[(current_page - 1) * nb_per_page:current_page * nb_per_page]]))
        embed.set_footer(text=f'{current_page} \\ {max_page}')
        await ctx.respond(embed=embed)
        msg = await ctx.interaction.original_message()

        if max_page > 1:
            # Page handler
            left_emoji = '\U00002B05'
            right_emoji = '\U000027A1'
            await msg.add_reaction(left_emoji)
            await msg.add_reaction(right_emoji)

            def check(reaction, user):
                return user != self.bot.user and (
                        str(reaction.emoji) == left_emoji or str(reaction.emoji) == right_emoji) \
                       and reaction.message.id == msg.id

            timeout = False

            while not timeout:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reaction(left_emoji)
                    await msg.clear_reaction(right_emoji)
                    timeout = True
                else:
                    old_page = current_page
                    if reaction.emoji == left_emoji:
                        current_page = current_page - 1 if current_page > 1 else max_page

                    if reaction.emoji == right_emoji:
                        current_page = current_page + 1 if current_page < max_page else 1

                    await msg.remove_reaction(reaction.emoji, user)

                    # Refresh embed message with the new text
                    if old_page != current_page:
                        embed = discord.Embed(title=title,
                                              description='\n'.join([badge for badge in badges_text[(current_page - 1) * nb_per_page:current_page * nb_per_page]]))
                        embed.set_footer(text=f'{current_page} \\ {max_page}')
                        await msg.edit(embed=embed)
