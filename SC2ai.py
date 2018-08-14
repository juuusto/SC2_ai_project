#This is bot used to train the protoss bot for the blink stalker all-in


import sc2
from sc2 import run_game, maps, Race, Difficulty, position
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
        await self.build_MM() # builds marines
        await self.build_orbitals()#not working
        await self.drop_mules()#not working
        await self.build_reactorsandtechlabs() #build reactors
        await self.intel() #used in drawing what the ai sees
        await self.build_factory() #build factory
        await self.build_starport() #build starport
        await self.attack() # attacking algorithm
        await self.build_medivacs() #medivacs
        await self.lower_depos() #lower depos
        await self.scout() # scouting
        



    async def build_workers(self):
        if self.units(SCV).amount < (self.units(COMMANDCENTER).amount*22):
            for cc in self.units(COMMANDCENTER).ready.noqueue:
                if self.can_afford(SCV):
                    await self.do(cc.train(SCV))

    async def lower_depos(self):
        for depos in self.units(SUPPLYDEPOT):
           await self.do(depos(MORPH_SUPPLYDEPOT_LOWER))

    async def build_SUPPLYDEPOS(self):
        if (self.supply_left < 5 and not self.already_pending(SUPPLYDEPOT)) or (self.supply_used > 50 and self.supply_left < 8):
            ccs = self.units(COMMANDCENTER).ready
            if ccs.exists:
                if self.can_afford(SUPPLYDEPOT):
                    cc = ccs.first
                    await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))

    
    async def expand(self):
        if self.units(COMMANDCENTER).amount < 6 and self.can_afford(COMMANDCENTER) and self.units(SCV).amount >= self.units(COMMANDCENTER).amount * 15 :
            await self.expand_now()

    async def build_factory(self):
        if self.units(BARRACKS).ready and self.can_afford(FACTORY) and self.units(FACTORY).amount < 1:
            cc = self.units(COMMANDCENTER).ready.first
            await self.build(FACTORY, near=cc.position.towards(self.game_info.map_center, 8))

    async def build_starport(self):
        if self.units(FACTORY).ready and self.can_afford(STARPORT) and self.units(STARPORT).amount < 1:
            cc = self.units(COMMANDCENTER).ready.first
            await self.build(STARPORT, near=cc.position.towards(self.game_info.map_center, 8))

    async def build_reactorsandtechlabs(self):
        ratio = self.count_addons()
        for rax in self.units(BARRACKS).ready:
            if rax.add_on_tag == 0:
                if ratio == 0:
                    await self.do(rax.build(BARRACKSREACTOR))
                elif ratio < float(3.0/2.0):
                    await self.do(rax.build(BARRACKSTECHLAB))
                elif ratio >= float(3.0/2.0):
                    await self.do(rax.build(BARRACKSREACTOR))

    #returns a number that represents the ration of techlab to reactor, ideal ration is 3 *n_techlabs/2* n_reactors.
    def count_addons(self):
        reactors = 0
        techlabs = 0.1
        for rax in self.units(BARRACKS).ready:
            if rax.add_on_tag != 0:
                if self.units.find_by_tag(rax.add_on_tag).name == 'BarracksTechLab':
                    techlabs += 1.0
                else:
                    reactors += 1.0
        if reactors == 0:
            return 0
        else:
            return float(techlabs/reactors)

    def random_location_variance(self, enemy_start_location):
        x = enemy_start_location[0]
        y = enemy_start_location[1]

        x += ((random.randrange(-10, 10))/100) * enemy_start_location[0]
        y += ((random.randrange(-10, 10))/100) * enemy_start_location[1]

        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x > self.game_info.map_size[0]:
            x = self.game_info.map_size[0]
        if y > self.game_info.map_size[1]:
            y = self.game_info.map_size[1]

        go_to = position.Point2(position.Pointlike((x,y)))
        return go_to

    async def scout(self):
        if self.supply_used == 21:
            for scv in self.units(SCV).idle:
                enemy_location = self.enemy_start_locations[0]
                move_to = self.random_location_variance(enemy_location)
                await self.do(scv.move(move_to))
                break


    def find_target(self,state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def intel(self):
        game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)

        drawing_dictionary = {
                COMMANDCENTER: [15, (0, 255, 0)],
                SUPPLYDEPOT: [3, (20, 235, 0)],
                SCV: [1, (55, 200, 0)],
                REFINERY: [2, (55, 200, 0)],
                BARRACKS: [3, (200, 100, 0)],
                FACTORY: [3, (150, 150, 0)],
                STARPORT: [5, (255, 0, 0)],
                MEDIVAC: [2, (255, 100, 0)],
                MARINE: [1, (255, 140, 0)],
                MARAUDER: [1, (255, 180, 0)],
                BARRACKSTECHLAB: [3, (200, 160, 0)],
                BARRACKSREACTOR: [3, (200, 220, 0)],
        }

        for unit_type in drawing_dictionary:
            for unit in self.units(unit_type).ready:
                pos = unit.position
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), drawing_dictionary[unit_type][0], drawing_dictionary[unit_type][1], -1)


        main_bases = ["nexus", "commandcenter", "hatchery"]
        for enemy_building in self.known_enemy_structures:
            pos = enemy_building.position
            if enemy_building.name.lower() not in main_bases:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), 5, (200, 50, 212), -1)
        for enemy_building in self.known_enemy_structures:
            pos = enemy_building.position
            if enemy_building.name.lower() in main_bases:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), 15, (0, 0, 255), -1)

        for enemy_unit in self.known_enemy_units:

            if not enemy_unit.is_structure:
                worker_names = ["probe",
                                "scv",
                                "drone"]
                # if a worker, draw something not so aggresive :)
                pos = enemy_unit.position
                if enemy_unit.name.lower() in worker_names:
                    cv2.circle(game_data, (int(pos[0]), int(pos[1])), 1, (55, 0, 155), -1)
                else:
                    cv2.circle(game_data, (int(pos[0]), int(pos[1])), 3, (50, 0, 215), -1)




        flipped = cv2.flip(game_data, 0)
        resized = cv2.resize(flipped, dsize = None, fx= 2, fy=2)
        cv2.imshow('Intel', resized)
        cv2.waitKey(1)

        



    async def build_orbitals(self):
            if self.units(BARRACKS).ready.exists and self.can_afford(ORBITALCOMMAND):
                for cc in self.units(COMMANDCENTER): 
                   await self.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))


    async def drop_mules(self):
        for oc in self.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
            mfs = self.state.mineral_field.closer_than(10, oc)
            if mfs:
                mf = max(mfs, key=lambda x:x.mineral_contents)
                await self.do(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))


    async def build_refinery(self):
        if self.supply_used > 16 and self.units(REFINERY).amount < 4 :
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
        if self.units(BARRACKS).amount < 1 or (self.units(BARRACKS).amount < 2 * self.units(COMMANDCENTER).amount and self.supply_used > 35):
            ccs = self.units(COMMANDCENTER).ready
            if ccs.exists:
                if self.can_afford(BARRACKS):
                    cc = ccs.first
                    await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 15))


    async def build_MM(self):
        for rax in self.units(BARRACKS).ready.noqueue:
            if rax.has_add_on:
                if self.units.find_by_tag(rax.add_on_tag).name == 'BarracksTechLab':
                    if self.can_afford(MARAUDER):
                        await self.do(rax.train(MARAUDER))
                elif self.units.find_by_tag(rax.add_on_tag).name == 'BarracksReactor':
                    if self.can_afford(MARINE):
                        await self.do(rax.train(MARINE))
                        if self.can_afford(MARINE):
                            await self.do(rax.train(MARINE))
            elif self.supply_used < 30 or self.supply_used > 180:
                if self.can_afford(MARINE):
                    await self.do(rax.train(MARINE))


    async def build_medivacs(self):
        for sp in self.units(STARPORT).ready.noqueue:
            if not self.can_afford(MEDIVAC):
                break
            await self.do(sp.train(MEDIVAC))

    async def attack(self):
        if self.supply_used > 150:
            for unit in self.units(MARINE).idle:
                await self.do(unit.attack(self.find_target(self.state)))
            for unit in self.units(MEDIVAC).idle:
                await self.do(unit.attack(self.find_target(self.state)))
            for unit in self.units(MARAUDER).idle:
                await self.do(unit.attack(self.find_target(self.state)))
        elif self.known_enemy_units.closer_than(50,self.units(COMMANDCENTER)).first:
            if len(self.known_enemy_units) > 0:
                for unit in self.units(MARINE).idle:
                    await self.do(unit.attack(random.choice(self.known_enemy_units)))
                for unit in self.units(MEDIVAC).idle:
                    await self.do(unit.attack(random.choice(self.known_enemy_units)))
                for unit in self.units(MARAUDER).idle:
                    await self.do(unit.attack(random.choice(self.known_enemy_units)))
            

#run game with bot        
run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Terran, TerranBot()),
    Computer(Race.Protoss, Difficulty.Hard)
], realtime=False)
