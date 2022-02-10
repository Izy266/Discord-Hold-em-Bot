import discord
from discord.ext import commands
from collections import Counter
import asyncio
import random

client = commands.Bot(command_prefix='.')
f = open("token.txt", "r")
token = f.read()
f.close()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_member_join(member):
    print(f'{member} has joined a server.')


@client.event
async def on_member_remove(member):
    print(f'{member} has left a server')


@client.command()
async def ping(ctx):
    await ctx.send(f'{round(client.latency * 1000)}ms')


@client.command()
async def clear(ctx, amount=1000):
    await ctx.channel.purge(limit=amount)

@client.command()
async def stop(message):
    None

@client.command()
async def start(message):
    game_starter = message.author
    channel = message.channel
    end_game = 0
    timer = 20
    msg = await channel.send(f'React to thumbs up emote to join game! You have {timer} seconds left')
    await msg.add_reaction('👍')

    class Player:
        def __init__(self, player_name, balance, cards_in_hand, full_hand, full_hand_values, broke, in_pot,
                     max_win, score):
            self.name = player_name
            self.balance = balance
            self.cards_in_hand = cards_in_hand
            self.in_pot = in_pot
            self.full_hand = full_hand
            self.full_hand_values = full_hand_values
            self.max_win = max_win
            self.score = score
            self.broke = broke

    value_dict = {
        "J": '11',
        "Q": '12',
        "K": '13',
        "A": '14'
    }

    def card_value(card):
        if card[:-1] in value_dict:
            return value_dict[card[:-1]]
        else:
            return card[:-1]

    def card_suit(card):
        return card[-1]

    players_with_money = []
    users = []
    players_list = []
    starting_player = 0
    balance = 1000
    small_blind = 20
    big_blind = 40

    def check(reaction, user):
        users.append(user)
        players_with_money.append(str(user))
        if 'Holdem Bot#0264' in players_with_money:
            del users[players_with_money.index('Holdem Bot#0264')]
            players_with_money.remove('Holdem Bot#0264')
        return not user.bot and str(reaction.emoji) == '👍' and reaction.count == 3


    async def reactions_check(timer):
        try:
            await client.wait_for('reaction_add', timeout=timer, check=check)

        except asyncio.TimeoutError:
            None

    async def countdown(timer):
            while timer > 0:
                timer -= 1
                await msg.edit(content=f'React to thumbs up emote to join game! You have `{timer}` seconds left')
                await asyncio.sleep(1)

    _, pending = await asyncio.wait([reactions_check(timer), countdown(timer)], return_when=asyncio.FIRST_COMPLETED)
    for future in pending:
        future.cancel()

    await msg.edit(content=f'React to thumbs up emote to join game! You have 0 seconds left')

    for i in users:
        players = Player(str(i), balance, [], [], [], 0, 0, 0, 0)
        players_list.append(players)

    while len(players_with_money) > 1 and end_game == 0:
        card_values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        card_suits = ['c', 'h', 's', 'd']
        deck = ([value + suit for value in card_values for suit in card_suits])
        random.shuffle(deck)
        cards_on_table = []
        players_fold = []
        active_players = []
        round_counter = 0
        total_pot_list = []
        total_pot = 0
        solo_counter = 0

        for i in range(len(players_list)):
            active_players.append(players_list[i])
            players_list[i].cards_in_hand = [deck.pop(), deck.pop()]
            await users[i].send(f'Your cards are ```{players_list[i].cards_in_hand}```')
            await users[i].send(f'Starting Balance: {players_list[i].balance} | Big blinds = ${big_blind} | Small '
                                f'blinds = ${small_blind}')

        players_list = players_list[starting_player:] + players_list[:starting_player]

        while round_counter < 4:
            inner_round_counter = 0
            player_counter = len(players_list)
            inner_players_with_money = []

            if round_counter > 0:
                total_pot_list.append(total_pot)

            for i in range(player_counter):
                players_list[i].in_pot = 0
            if round_counter == 0:
                cur_call = big_blind
                total_pot = big_blind + small_blind
                players_list[-1].in_pot = big_blind
                players_list[-2].in_pot = small_blind
                players_list[-1].balance = players_list[-1].balance - players_list[-1].in_pot
                players_list[-2].balance = players_list[-2].balance - players_list[-2].in_pot
            else:
                cur_call = 0

            for i in active_players:
                if i.balance > 0:
                    inner_players_with_money.append(i)

                if i.broke == 1:
                    if len(total_pot_list) >= 2:
                        i.max_win = (i.max_win * len(active_players)) + total_pot_list[-2]
                    else:
                        i.max_win = i.max_win * len(active_players)

                i.broke = 0

            while inner_round_counter < player_counter:
                raise_loc = []

                embed = discord.Embed(title="Texas Hold'em", url="https://en.wikipedia.org/wiki/Texas_hold_%27em",
                                      description="Welcome to the Texas Hold'em Discord Bot! GLHF!",
                                      color=0x59bfff)
                embed.set_thumbnail(url="https://i.ibb.co/Wn8zWjd/holdem-bot.png")

                for i in range(len(players_list)):
                    embed.add_field(name=f"{players_list[i].name}",
                                    value=f"Balance: {players_list[i].balance}\nIn pot: {players_list[i].in_pot}",
                                    inline=True)

                embed.add_field(name="Cards", value=(f"Cards on table: {cards_on_table}"), inline=False)
                # embed.set_image(url="https://i.ibb.co/8NZPdmD/Clubs.png")
                embed.set_footer(text=f"Pot: {total_pot}")

                await message.send(embed=embed)

                if players_list[inner_round_counter].name not in players_fold and players_list[
                    inner_round_counter].balance > 0 and len(inner_players_with_money) > 1:
                    left_to_check = cur_call - players_list[inner_round_counter].in_pot

                    await channel.send(f"```{players_list[inner_round_counter].name}, (C)heck, (B)et or (F)old. "
                                       f"{left_to_check} more to check```")

                    def check(msg):
                        if str(msg.author) == str(players_list[inner_round_counter].name):
                            if msg.content.lower() in ["c", "f"]:
                                return True
                            elif msg.content.lower() == "b":
                                if players_list[inner_round_counter].balance > cur_call - players_list[inner_round_counter].in_pot:
                                    return True

                    msg = await client.wait_for("message")

                    while not check(msg):
                        if (str(msg.author) != str(players_list[inner_round_counter].name)) or ((str(msg.author) != str(game_starter)) and msg.content.lower() != ".stop" and str(msg.author) != str(players_list[inner_round_counter].name)):
                            await channel.send(f'It\'s {str(players_list[inner_round_counter].name)}\'s turn to ('
                                               f'C)heck, (B)et or (F)old')
                        elif ((str(msg.author) != str(game_starter)) and msg.content.lower() == ".stop"):
                            await channel.send(f'Only the player who started the game, {game_starter}, can end the game')
                        elif ((str(msg.author) == str(game_starter)) and msg.content.lower() == ".stop"):
                            await channel.send(f'The game will end upon round completion')
                            end_game = 1
                        elif msg.content.lower() not in ["c", "b", "f"]:
                            await channel.send(f"Please send \"C\", \"B\", or \"F\" to (C)heck, (B)et or (F)old "
                                               f"respectively")
                        elif players_list[inner_round_counter].balance <= cur_call - players_list[inner_round_counter].in_pot:
                            await channel.send(f'You do not have enough balance to bet an amount greater than your current call, {cur_call - players_list[inner_round_counter].in_pot}')

                        msg = await client.wait_for('message')

                    if msg.content.lower() == "c":
                        await channel.send("You said check")
                        if players_list[inner_round_counter].balance >= left_to_check:
                            players_list[inner_round_counter].in_pot += left_to_check
                            players_list[inner_round_counter].balance -= left_to_check
                            total_pot += left_to_check
                        elif players_list[inner_round_counter].balance <= left_to_check:
                            players_list[inner_round_counter].max_win = players_list[inner_round_counter].balance +\
                                                                        players_list[inner_round_counter].in_pot
                            players_list[inner_round_counter].in_pot += players_list[inner_round_counter].balance
                            total_pot += players_list[inner_round_counter].balance
                            players_list[inner_round_counter].balance = 0
                            players_list[inner_round_counter].broke = 1

                    elif msg.content.lower() == "b":
                        await channel.send("How much?")
                        msg = await client.wait_for('message')
                        max_balance = 0

                        for i in active_players:
                            if i != players_list[inner_round_counter] and i.balance > max_balance:
                                max_balance = i.balance

                        def check(msg):
                            if str(msg.content).isdigit() is True and str(msg.author) == str(players_list[inner_round_counter].name):
                                if int(msg.content) >= big_blind:
                                    if players_list[inner_round_counter].balance >= int(msg.content) and cur_call - players_list[inner_round_counter].in_pot <= int(msg.content) <= max_balance + (cur_call - players_list[inner_round_counter].in_pot):
                                        return True
                                elif players_list[inner_round_counter].balance < big_blind and players_list[inner_round_counter].balance == int(msg.content):
                                    if players_list[inner_round_counter].balance >= int(msg.content) and int(msg.content) <= max_balance + (cur_call - players_list[inner_round_counter].in_pot):
                                        return True

                        while not check(msg):
                            if not str(msg.content).isdigit():
                                await channel.send("Please enter a valid number")
                            elif players_list[inner_round_counter].balance < big_blind and \
                                    players_list[inner_round_counter].balance != int(msg.content):
                                await channel.send(f"You must go all in since you don't have enough balance to "
                                                   f"bet greater the big blind: '{big_blind}`")
                            elif int(msg.content) < big_blind:
                                await channel.send(f"You must bet an amount larger than the big blind: "
                                                   f"```{big_blind}```")
                            elif int(msg.content) > max_balance + (cur_call - players_list[inner_round_counter].in_pot):
                                await channel.send(f"You can not bed more than {max_balance + (cur_call - players_list[inner_round_counter].in_pot)} due to the balance of other players")
                            elif int(msg.content) <= cur_call - players_list[inner_round_counter].in_pot:
                                await channel.send(f"You must bet an amount larger than your current call: ```{cur_call - players_list[inner_round_counter].in_pot}```")
                            elif players_list[inner_round_counter].balance < big_blind and players_list[inner_round_counter].balance != int(msg.content):
                                await channel.send(f"Since your balance is less than the minimum bet/big blind, {big_blind}, you must go all in to bet")

                            msg = await client.wait_for("message")

                        if int(msg.content) == cur_call - players_list[inner_round_counter].in_pot:
                            await channel.send(f"Your bet = current call. Simply send \"C\" next time to (C)heck")

                        raise_loc.append(inner_round_counter)

                        players_list[inner_round_counter].in_pot += int(msg.content)
                        players_list[inner_round_counter].balance -= int(msg.content)
                        cur_call = players_list[inner_round_counter].in_pot
                        total_pot += int(msg.content)

                    elif msg.content.lower() == "f":
                        players_fold.append(players_list[inner_round_counter].name)
                        active_players.remove(players_list[inner_round_counter])
                        await channel.send("You said fold")

                if len(raise_loc) > 0 and inner_round_counter == player_counter:
                    player_counter = raise_loc[-1]
                    inner_round_counter = 0
                    if raise_loc[-1] == 0:
                        player_counter = len(players_list)
                        inner_round_counter = 1

                if len(active_players) == 1:
                    inner_round_counter = player_counter
                    await channel.send(f'{active_players[0].name} won!\n(S)how or (M)uck?')

                    def check(msg):
                        return str(msg.author) == str(active_players[0].name) and \
                               msg.content.lower() in ["s", "m"]

                    msg = await client.wait_for("message")

                    while not check(msg):
                        if str(msg.author) != str(players_list[inner_round_counter].name):
                            await channel.send(f'It\'s {str(active_players[0].name)}\'s turn to (S)how or (M)uck')
                        elif msg.content.lower() not in ["s", "m"]:
                            await channel.send(f'Please send \"S\" or \"M\" to (S)how or (M)muck respectively')

                        msg = await client.wait_for("message")

                    if msg.content.lower() == "s":
                        await channel.send(f'{active_players[0].name}\'s Cards: {active_players[0].cards_in_hand}')

                    active_players[0].balance += total_pot
                    total_pot = 0
                    round_counter = 4

                for i in active_players:
                    if i.balance <= 0 and i in inner_players_with_money:
                        inner_players_with_money.remove(i)

                if len(inner_players_with_money) <= 1:
                    if solo_counter == 0:
                        while len(cards_on_table) < 5:
                            cards_on_table.append(deck.pop())
                        inner_round_counter = player_counter - 2
                        round_counter = 3
                    solo_counter = 1

                inner_round_counter += 1

            if round_counter < 3 and len(cards_on_table) < 5:
                if round_counter == 0:
                    cards_on_table.extend([deck.pop(), deck.pop(), deck.pop()])
                else:
                    cards_on_table.append(deck.pop())

            round_counter += 1

        starting_player = 1

        for i in range(len(players_list)):
            if players_list[i].name not in players_fold:
                players_list[i].full_hand = players_list[i].cards_in_hand + cards_on_table

        def check_hand(hand, name):
            hand_values = []
            for i in range(len(hand)):
                hand_values.append(card_value(hand[i]))
            value_histogram = Counter(hand_values).most_common()

            def sort_hand(x_hand):
                x_hand_sorted = []
                x_hand_values = []
                x_hand_values_unsorted = []
                indices = []
                for i in x_hand:
                    x_hand_values_unsorted.append(int(card_value(i)))
                    x_hand_values.append(int(card_value(i)))
                    x_hand_values.sort()
                for i in x_hand_values:
                    indices.append(x_hand_values_unsorted.index(i))
                    x_hand_values_unsorted[indices[-1]] = 0
                for i in range(len(x_hand)):
                    x_hand_sorted.append(x_hand[indices[i]])
                return x_hand_sorted

            def value_hand(v_hand):
                hand_values = []
                for i in v_hand:
                    hand_values.append(card_value(i))
                return hand_values

            def straight_check(s_list):
                straight_cards = []
                straight_cards_values = []
                straight_check_list = []
                for s in s_list:
                    straight_cards_values.append(int(card_value(s)))
                    if int(card_value(s)) not in straight_check_list:
                        straight_check_list.append(int(card_value(s)))
                straight_check_list.sort()
                counter = len(straight_check_list) - 1
                while (counter - 4) >= 0:
                    if int(straight_check_list[counter]) - int(straight_check_list[counter - 4]) == 4:
                        for i in range(len(straight_check_list[:counter + 1][-5:])):
                            if straight_check_list[:counter + 1][-5:][i] in straight_cards_values:
                                straight_cards.append(
                                    s_list[straight_cards_values.index(straight_check_list[:counter + 1][-5:][i])])
                        return straight_cards
                    counter -= 1
                low_straight = [14, 2, 3, 4, 5]
                if set(low_straight).issubset(straight_check_list):
                    for i in s_list:
                        if int(card_value(i)) in low_straight and int(card_value(i)) not in straight_cards:
                            straight_cards.append(i)
                    return straight_cards

            def flush_check(f_list):
                f_list_suits = []
                for i in f_list:
                    f_list_suits.append(card_suit(i))
                suit_histogram = Counter(f_list_suits).most_common()
                flush_cards = []
                if suit_histogram[0][1] > 4:
                    for i in range(len(f_list)):
                        if card_suit(f_list[i]) == suit_histogram[0][0]:
                            flush_cards.append(f_list[i])
                    return flush_cards

            def straight_flush_check(sf_list):
                if flush_check(sf_list):
                    if straight_check(flush_check(sf_list)):
                        return straight_check(flush_check(sf_list))

            if straight_flush_check(hand):
                if int(card_value(straight_flush_check(hand)[0])) == 10:
                    name.score = 9
                    name.full_hand_values = value_hand(straight_flush_check(hand))
                    return straight_flush_check(hand)

            if straight_flush_check(hand):
                name.score = 8
                name.full_hand_values = value_hand(straight_flush_check(hand))
                return straight_flush_check(hand)

            if value_histogram[0][1] == 4:
                four_kind_hand = []

                for i in hand:
                    if card_value(i) == value_histogram[0][0]:
                        four_kind_hand.append(i)
                name.score = 7
                name.full_hand_values = value_hand(four_kind_hand)
                return four_kind_hand

            if value_histogram[0][1] == 3 and value_histogram[1][1] >= 2:
                full_house_hand = []
                rem_fh_counter = 0
                if value_histogram[0][1] == 3 and value_histogram[1][1] == 3:
                    if int(value_histogram[1][0]) > int(value_histogram[0][0]):
                        for i in hand:
                            if card_value(i) == value_histogram[1][0]:
                                full_house_hand.append(i)
                        for i in hand:
                            if rem_fh_counter < 2 and card_value(i) == value_histogram[0][0]:
                                full_house_hand.append(i)
                                rem_fh_counter += 1
                    else:
                        for i in hand:
                            if card_value(i) == value_histogram[0][0]:
                                full_house_hand.append(i)
                        for i in hand:
                            if rem_fh_counter < 2 and card_value(i) == value_histogram[1][0]:
                                full_house_hand.append(i)
                                rem_fh_counter += 1
                else:
                    for i in hand:
                        if card_value(i) == value_histogram[0][0]:
                            full_house_hand.append(i)
                    for i in hand:
                        if card_value(i) == value_histogram[1][0]:
                            full_house_hand.append(i)
                name.score = 6
                name.full_hand_values = value_hand(full_house_hand)
                return full_house_hand

            if flush_check(hand):
                flush_hand = sort_hand(flush_check(hand))
                flush_hand = flush_hand[-5:]
                name.score = 5
                name.full_hand_values = value_hand(flush_hand)
                return flush_hand

            if straight_check(hand):
                name.score = 4
                name.full_hand_values = value_hand(straight_check(hand))
                return straight_check(hand)

            if value_histogram[0][1] == 3 and value_histogram[1][1] == 1 or value_histogram[1][1] >= 3:
                three_kind_hand = []
                sorted_hand = []
                for i in hand:
                    if card_value(i) == value_histogram[0][0]:
                        three_kind_hand.append(i)
                for i in hand:
                    if card_value(i) != value_histogram[0][0]:
                        sorted_hand.append(i)
                sorted_hand = sort_hand(sorted_hand)
                three_kind_hand += [sorted_hand[-1], sorted_hand[-2]]
                name.score = 3
                name.full_hand_values = value_hand(three_kind_hand)
                return three_kind_hand

            if value_histogram[0][1] == 2 and value_histogram[1][1] == 2:
                two_pair_hand = []
                hand_values = []
                pair_one = 1
                pair_two = 0
                if value_histogram[2][1] == 2:
                    if int(value_histogram[0][0]) < int(value_histogram[1][0]) and int(value_histogram[0][0]) < int(
                            value_histogram[2][0]):
                        pair_one = 2
                        pair_two = 1
                    elif int(value_histogram[1][0]) < int(value_histogram[0][0]) and int(value_histogram[1][0]) < int(
                            value_histogram[2][0]):
                        pair_one = 2
                for i in hand:
                    if card_value(i) == value_histogram[pair_one][0]:
                        two_pair_hand.append(i)
                for i in hand:
                    if card_value(i) == value_histogram[pair_two][0]:
                        two_pair_hand.append(i)
                for i in hand:
                    if i not in two_pair_hand:
                        hand_values.append(int(card_value(i)))
                hand_values.sort()
                for i in hand:
                    if int(card_value(i)) == hand_values[-1]:
                        two_pair_hand.append(i)
                name.score = 2
                name.full_hand_values = value_hand(two_pair_hand)
                return two_pair_hand

            if value_histogram[0][1] == 2 and value_histogram[1][1] == 1:
                pair_hand = []
                sorted_hand = []
                for i in hand:
                    if card_value(i) == value_histogram[0][0]:
                        pair_hand.append(i)
                for i in hand:
                    if card_value(i) != value_histogram[0][0]:
                        sorted_hand.append(i)
                sorted_hand = sort_hand(sorted_hand)
                pair_hand += [sorted_hand[-1], sorted_hand[-2], sorted_hand[-3]]
                name.score = 1
                name.full_hand_values = value_hand(pair_hand)
                return pair_hand

            name.score = 0
            name.full_hand_values = value_hand(sort_hand(hand)[-5:])
            return sort_hand(hand)[-5:]

        score_dict = {
            0: 'High Card',
            1: 'Pair',
            2: 'Two Pair',
            3: 'Three of a Kind',
            4: 'Straight',
            5: 'Flush',
            6: 'Full House',
            7: 'Four of a Kind',
            8: 'Straight Flush',
            9: 'Royal Flush'
        }

        if len(cards_on_table) == 5 and len(active_players) > 1:
            scores_list = []
            player_ranking = []

            for i in active_players:
                i.full_hand = check_hand(i.full_hand, i)

            for i in active_players:
                scores_list.append(i.score)

            scores_histogram = Counter(scores_list).most_common()
            scores_histogram.sort(key=lambda x: x[0], reverse=True)

            active_player_names = []
            for i in active_players:
                active_player_names.append(i.name)

            for i in scores_histogram:
                if i[1] == 1:
                    player_ranking.append(active_players[scores_list.index(i[0])])
                elif i[1] > 1:
                    x = 0
                    tied_players = []
                    tied_player_ranking = []
                    tied_hand_values = []
                    tie_breaker = []

                    while x < len(active_players) and i[0] in scores_list:
                        tie_breaker.append(active_players[scores_list.index(i[0])])
                        scores_list[scores_list.index(i[0])] = -1
                        x += 1

                    for j in tie_breaker:
                        tied_hand_values.append(tuple(j.full_hand_values))

                    tied_hand_values = tuple(tied_hand_values)

                    tie_histogram = Counter(tied_hand_values).most_common()
                    tie_histogram.sort(key=lambda x: x[0], reverse=True)

                    for j in tie_histogram:
                        if j[1] == 1:
                            for k in tie_breaker:
                                if j[0] == tuple(k.full_hand_values):
                                    player_ranking.append(k)
                        elif j[1] > 1:
                            for k in tie_breaker:
                                if j[0] == tuple(k.full_hand_values):
                                    tied_players.append(k)

                            for k in tied_players:
                                tied_player_ranking.append(k)

                            player_ranking.append(tied_player_ranking)

            while total_pot > 0:
                x = 0
                if type(player_ranking[x]) == list:
                    for i in player_ranking[x]:
                        if i.max_win == 0 or i.max_win >= total_pot / len(player_ranking[x]):
                            i.balance += total_pot / len(player_ranking[x])
                            total_pot -= total_pot / len(player_ranking[x])
                        else:
                            i.balance += i.max_win
                            total_pot -= i.max_win
                else:
                    if player_ranking[x].max_win == 0 or player_ranking[x].max_win >= total_pot:
                        player_ranking[x].balance += total_pot
                        total_pot = 0
                    else:
                        player_ranking[x].balance += player_ranking[x].max_win
                        total_pot -= player_ranking[x].max_win
                x += 1

            if type(player_ranking[0]) == list:
                for i in player_ranking[0]:
                    await channel.send(f'{i.name} won with a {score_dict[i.score]}.')
            else:
                await channel.send(f'{player_ranking[0].name} won with a {score_dict[player_ranking[0].score]}')

            print(f'players_with_money : {players_with_money}')

            for i in active_players:
                await channel.send(f'{i.name}\'s hand : {i.full_hand}')
                await channel.send(f'{i.name}\'s balance: {i.balance}')
                if i.balance == 0:
                    players_with_money.remove(i.name)

            # for i in active_players:
            #     print(f'{i.name} max_win : {i.max_win}')

client.run(token)
