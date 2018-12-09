import sc2
from sc2 import run_game, maps, Race, Difficulty, Result, unit_command, position
from sc2.player import Bot, Computer
from sc2.constants import DRONE, HATCHERY, LARVA, OVERLORD, ZERGLING, SPAWNINGPOOL, QUEEN
from sc2.ids.ability_id import EFFECT_INJECTLARVA
# from sc2.unit import build_progress
from sc2.data import race_townhalls
import random
import numpy as np
import time

from sc2 import bot_ai
class Zergbot(sc2.BotAI):
    # def __init__(self):

    # def on_end(self, game_result):
    #     print('--- on_end called ---')
    #     print(game_result)
    #
    #     if game_result == Result.Victory:
    #         np.save("train_data/{}.npy".format(str(int(time.time()))), np.array(self.train_data))

    async def on_step(self, iteration):
        await self.distribute_workers()
        if iteration < 1:
            await self.build_workers()
            await self.build_overlords()
        if self.supply_used > 15:
            await self.build_spawningpool()
        await self.larva_manager()
        await self.attack_start_location()
        await self.expand()
        if self.units(QUEEN).amount > 0:
            await self.inject_hatch()


    async def larva_manager(self):
        if self.supply_left < 5:
            await self.build_overlords()
        if self.units(DRONE).amount < self.units(HATCHERY).amount * 16:
            await self.build_workers()
        if self.units(QUEEN).amount + self.already_pending(QUEEN) < self.units(HATCHERY).amount + self.already_pending(HATCHERY)\
                and self.units(SPAWNINGPOOL).ready.exists:
            await self.build_queen()
        await self.build_zerglings()


    async def build_workers(self):
        larvae = self.units(LARVA)
        if self.can_afford(DRONE) and larvae.exists and self.supply_left > 1: #builds two because it does not check if one is pending
            await self.do(larvae.random.train(DRONE))

    async def build_overlords(self):
        if self.can_afford(OVERLORD) and self.units(LARVA).exists and not self.already_pending(OVERLORD):
            await self.do(self.units(LARVA).random.train(OVERLORD))

    async def build_queen(self):
        counter = 0
        if self.units(SPAWNINGPOOL):
            for hatchery in self.units(HATCHERY).ready.noqueue:
                if self.can_afford(QUEEN):
                    await self.do(hatchery.train(QUEEN))
            # print(" Start of Test Queen block --------------------------------------")
            # print("already_pending HATCHERY: " + str(self.already_pending(HATCHERY)))
            # print("HATCHERY amount: " + str(self.units(HATCHERY).amount))
            # print("already_pending QUEENS: " + str(self.already_pending(QUEEN)))
            # print("QUEENS amount: " + str(self.units(QUEEN).amount))

    async def build_zerglings(self):
        if self.can_afford(ZERGLING) and self.units(LARVA).exists and self.units(SPAWNINGPOOL).ready.exists \
                and self.supply_left >= 2:
            await self.do(self.units(LARVA).random.train(ZERGLING))

    async def attack_start_location(self):
        if self.units(ZERGLING).amount > 12:
            for zerging in self.units(ZERGLING).idle:
                await self.do(zerging.attack(self.enemy_start_locations[0]))
            return

    async def build_spawningpool(self):
        if not (self.units(SPAWNINGPOOL).exists or self.already_pending(SPAWNINGPOOL)):
            if self.can_afford(SPAWNINGPOOL):
                await self.build(SPAWNINGPOOL, near=self.townhalls.first)

    async def build_macro_hatch(self):
        if self.minerals > 450 and not self.already_pending(HATCHERY):
            try :
                await self.build(HATCHERY, near=self.townhalls.first)
                print("Test: build_macro_hatch was called")
            except:
                print("build_macro_hatch Failed")

    async def expand(self):
        if self.units(HATCHERY).amount * 14 < self.units(DRONE).amount and self.can_afford(HATCHERY) \
                and not self.already_pending(HATCHERY) and self.units(HATCHERY).amount < 3:
            await self.expand_now()

    async def inject_hatch(self):
        for hatchery in self.units(HATCHERY):
            this_queen = self.units(QUEEN).closest_to(hatchery)
            if this_queen.energy >= 25 and this_queen.build_progress == 1 and hatchery.build_progress ==1: #should fix the flow of resource errors
                await self.do(this_queen(EFFECT_INJECTLARVA, hatchery))


run_game(maps.get("AbyssalReefLE"), [Bot(Race.Zerg, Zergbot()), Computer(Race.Terran, Difficulty.Easy)], realtime = False)
