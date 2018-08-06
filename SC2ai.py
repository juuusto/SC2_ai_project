import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit

import random
import numpy as np 
import cv2


class TerranBot(sc2.BotAI):
    async def on_step(self, iteration):
        await self.distribute_workers()  #worker distribution, found in sc2/bot_ai.py
        await self.build_workers() #worker building
        await self.build_SUPPLYDEPOS() #depo building
        await self.build_refinery() #build refineries
        await self.expand() #expand
        await self.build_barracks() # builds rax
        await self.build_marines() # builds marines
        await self.build_orbitals()#not working
        await self.drop_mules()#not working
        await self.build_reactors() 
        await self.intel()
        await self.attack() # attacking algorithm



    async def build_workers(self):
        if self.units(SCV).amount < (self.units(COMMANDCENTER).amount*16):
            for cc in self.units(COMMANDCENTER).ready.noqueue:
                if self.can_afford(SCV):
                    await self.do(cc.train(SCV))


    async def build_SUPPLYDEPOS(self):
        if (self.supply_left < 5 and not self.already_pending(SUPPLYDEPOT)) or (self.supply_used > 80 and self.supply_left < 8):
            ccs = self.units(COMMANDCENTER).ready
            if ccs.exists:
                if self.can_afford(SUPPLYDEPOT):
                    cc = ccs.first
                    await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 6))

    
    async def expand(self):
        if self.units(COMMANDCENTER).amount < 4 and self.can_afford(COMMANDCENTER):
            await self.expand_now()


    async def build_reactors(self):
      for sp in self.units(BARRACKS).ready:
         if sp.add_on_tag == 0:
            if(self.can_afford(BARRACKSREACTOR)):
                await self.do(sp.build(BARRACKSREACTOR))


    def find_target(self,state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def intel(self):
        game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)
        for cc in self.units(COMMANDCENTER):
            cc_pos = cc.position
            cv2.circle(game_data, (int(cc_pos[0]), int(cc_pos[1])), 10, (255, 0, 0), -1)
        flipped = cv2.flip(game_data, 0)
        resized = cv2.resize(flipped, dsize = None, fx= 2, fy=2)
        cv2.imshow('Intel', resized)
        cv2.waitKey(1)

        



    async def build_orbitals(self):
            if self.units(UnitTypeId.BARRACKS).ready.exists and self.can_afford(UnitTypeId.ORBITALCOMMAND):
                for cc in self.units(UnitTypeId.COMMANDCENTER): 
                    self.do(cc.build(ORBITALCOMMAND))


    async def drop_mules(self):
        for oc in self.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
            mfs = self.state.mineral_field.closer_than(10, oc)
            if mfs:
                mf = max(mfs, key=lambda x:x.mineral_contents)
                self.do(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))


    async def build_refinery(self):
        if self.supply_used > 17 and self.units(REFINERY).amount < 2 :
            for cc in self.units(COMMANDCENTER).ready:
                vsg = self.state.vespene_geyser.closer_than(10.0, cc)
                for geyser in vsg:
                    if not self.can_afford(REFINERY):
                        break
                    worker = self.select_build_worker(geyser.position)
                    if worker is None:
                        break
                    if not self.units(REFINERY).closer_than(1.0, geyser).exists:
                        await self.do(worker.build(REFINERY, geyser))

    async def build_barracks(self):
        if self.units(BARRACKS).amount < 1 or (self.units(BARRACKS).amount < 3 * 2*self.units(COMMANDCENTER).amount and self.supply_used > 35):
            ccs = self.units(COMMANDCENTER).ready
            if ccs.exists:
                if self.can_afford(BARRACKS):
                    cc = ccs.first
                    await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 15))

    async def build_marines(self):
        for rax in self.units(BARRACKS).ready.noqueue:
            if not self.can_afford(MARINE):
                break
            await self.do(rax.train(MARINE))


    async def attack(self):
        if self.units(MARINE).amount > 70:
            for unit in self.units(MARINE).idle:
                await self.do(unit.attack(self.find_target(self.state)))
        elif self.units(MARINE).amount > 5:
            if len(self.known_enemy_units) > 0:
                for unit in self.units(MARINE).idle:
                    await self.do(unit.attack(random.choice(self.known_enemy_units)))
            

#run game with bot        
run_game(maps.get("(2)16-BitLE"), [
    Bot(Race.Terran, TerranBot()),
    Computer(Race.Protoss, Difficulty.Hard)
], realtime=True)