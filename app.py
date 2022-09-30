#-*- coding: utf-8 -*-

#https://www.smogon.com/stats/

#----user options----#

dynamax = True
only_strongest_moves = False
only_first_set = False
mew_mode = False

#No EVs / IVs, nature?


#--------------------# 

import csv
from os import write
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.log import Identified
from sqlalchemy.orm import session, sessionmaker, relationship
from math import floor
from sqlalchemy.sql import base
from flask import Flask
from flask import render_template

from sqlalchemy.sql.sqltypes import SmallInteger


class Pokemon:
    def __init__(self, id_, name, type_one, type_two, item, level, ability, hp, atk, def_, spa, spd, spe, ivs, g_max):
        self.id_ = id_
        self.name = name
        self.type_one = type_one
        self.type_two = type_two
        self.item = item
        self.level = level
        self.ability = ability
        self.hp = hp
        self.atk = atk
        self.def_ = def_
        self.spa = spa
        self.spd = spd
        self.spe = spe
        self.ivs = ivs
        self.spreads = []
        self.moves = []
        self.g_max = g_max

Base = declarative_base()

class Pokemon_DB(Base):
    __tablename__ = "pokemon"

    id = Column('id', Integer, primary_key=True)
    identifier = Column('identifier', String)
    species_id = Column('species_id', Integer)
    height = Column('height', Integer)
    weight = Column('weight', Integer)
    base_experience = Column('base_experience', Integer)
    order = Column('order', Integer)
    is_default = Column('is_default', Boolean)

class Pokemon_Moves(Base):
    __tablename__ = 'pokemon_moves'

    pokemon_id = Column('pokemon_id', Integer, primary_key=True)
    version_group_id = Column('version_group_id', Integer, primary_key=True)
    move_id = Column('move_id', Integer, primary_key=True)

class Pokemon_Species(Base):
    __tablename__ = 'pokemon_species'

    id = Column('id', Integer, primary_key=True)
    identifier = Column('identifier', String)
    generation_id = Column('generation_id', Integer)
    evolves_from_species_id = Column('evolves_from_species_id', Integer)
    evolution_chain_id = Column('evolution_chain_id', Integer)
    order = Column('order', Integer)

class Pokemon_Stats(Base):
    __tablename__ = "pokemon_stats"

    pokemon_id = Column('pokemon_id', Integer, primary_key=True)
    stat_id = Column('stat_id', Integer, primary_key=True)
    base_stat = Column('base_stat', Integer)
    effort = Column('effort', Integer)

class Pokemon_Types(Base):
    __tablename__ = "pokemon_types"

    pokemon_id = Column('pokemon_id', Integer, primary_key=True)
    type_id = Column('type_id', Integer)
    slot = Column('slot', Integer, primary_key=True)

class Moves(Base):
    __tablename__ = "moves"

    id = Column('id', Integer, primary_key=True)
    identifier = Column('identifier', String)
    type_id = Column('type_id', Integer)
    power = Column('power', SmallInteger)
    pp = Column('pp', SmallInteger)
    accuracy = Column('accuracy', SmallInteger)
    target_id = Column('target_id', Integer)
    damage_class_id = Column('damage_class_id', Integer)
    effect_id = Column('effect_id', Integer)
    effect_chance = Column('effect_chance', Integer)

#Remove later - just for testing
class Move_Targets(Base):
    __tablename__ = "move_targets"

    id = Column('id', Integer, primary_key=True)
    identifier = Column('identifier', String)

class Type_Efficacy(Base):
    __tablename__ = "type_efficacy"

    damage_type_id = Column('damage_type_id', Integer, primary_key=True)
    target_type_id = Column('target_type_id', Integer, primary_key=True)
    damage_factor = Column('damage_factor', Integer)

class Natures(Base):
    __tablename__ = "natures"

    id = Column('id', Integer, primary_key=True)
    identifier = Column('identifier', String)
    decreased_stat_id = Column('decreased_stat_id', Integer)
    increased_stat_id = Column('increased_stat_id', Integer)

evs_str = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']

engine = create_engine("sqlite:///pokedex.sqlite")
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()


def parse_spread(spread):
    nature = spread.split(':')[0]
    evs = spread.split(':')[1].split('/')
    evs_list = []
    for x in range(6):
        if evs[x] != '0':
            evs_list.append(evs[x] + ' ' + evs_str[x])
    if evs_list == []:
        evs_list = None
    return nature, evs

def get_true_stat(stat_id, pokemon, spread):
    spread = parse_spread(spread)
    nature = spread[0]
    evs = spread[1]
    if nature != None:
        nature_data = session.query(Natures).filter_by(identifier=nature.lower()).first()
        if nature_data.decreased_stat_id == stat_id:
            nature = 0.9
        elif nature_data.increased_stat_id == stat_id:
            nature = 1.1
        else:
            nature = 1
    else:
        nature = 1
    if pokemon.level == 0:
        level = 50
    else:
        level = pokemon.level
    if stat_id == 1:
        stat_str = 'HP'
        base_stat = pokemon.hp
    elif stat_id == 2:
        stat_str = 'Atk'
        base_stat = pokemon.atk
    elif stat_id == 3:
        stat_str = 'Def'
        base_stat = pokemon.def_
    elif stat_id == 4:
        stat_str = 'SpA'
        base_stat = pokemon.spa
    elif stat_id == 5:
        stat_str = 'SpD'
        base_stat = pokemon.spd
    elif stat_id == 6:
        stat_str = 'Spe'
        base_stat = pokemon.spe
    stat_iv = 31
    stat_str = evs_str[stat_id - 1]
    stat_ev = 0
    if evs != None:
        stat_ev = int(evs[stat_id - 1])

    if pokemon.ivs != None:
        for iv in pokemon.ivs:
            if iv.split(' ')[1] == stat_str:
                stat_iv = int(iv.replace(' ' + stat_str, ''))
    if stat_id == 1:
        #HP=true
        #true_stat = floor(floor(2 * base_stat + stat_iv + stat_ev) * level / 100 + level + 10)
        true_stat = floor(0.01 * (2 * base_stat + stat_iv + floor(0.25 * stat_ev)) * level) + level + 10
    else:
        true_stat = floor(floor(0.01 * ((2 * base_stat + stat_iv + floor(0.25 * stat_ev)) * level) + 5) * nature)
    #print(true_stat, stat_ev)
    return true_stat, stat_ev

def get_pokemon(name):
    if name.split('-')[-1] == 'Gmax':
        name = name.replace('-Gmax', '')
        g_max = True
    else:
        g_max = False
    #print(name)
    if name == 'Mimikyu':
        name = 'mimikyu-disguised'
    elif name == 'Thundurus':
        name = 'thundurus-incarnate'
    elif name == 'Tornadus':
        name = 'tornadus-incarnate'
    elif name == 'Landorus':
        name = 'landorus-incarnate'
    elif name == 'Indeedee-F':
        name = 'indeedee-female'
    elif name == 'Indeedee':
        name = 'indeedee-male'
    elif name == 'Urshifu':
        name = 'urshifu-single-strike'
    elif name == 'Zygarde':
        name = 'zygarde-complete'
    elif name == 'Necrozma-Dusk-Mane':
        name = 'necrozma-dusk'
    elif name == 'Necrozma-Dawn-Wings':
        name = 'necrozma-dawn'
    elif name == 'Giratina':
        name = 'giratina-altered'
    elif name == 'Meowstic':
        name = 'meowstic-male'
    elif name == 'Darmanitan-Galar':
        name = 'darmanitan-galar-standard'
    elif name == 'Aegislash':
        name = 'aegislash-shield'
    elif name == 'Toxtricity':
        name = 'toxtricity-amped'
    elif name == 'Zygarde-10%':
        name = 'zygarde-10'
        
    find_id = session.query(Pokemon_DB).filter_by(identifier=name.replace(' ', '-').replace('.', '').lower()).first()
    try:
        id_ = find_id.id
    except:
        print(name.replace(' ', '-').replace('.', '').lower(), "can't be found!")
    base_stats = session.query(Pokemon_Stats).filter_by(pokemon_id=id_)
    hp = base_stats[0].base_stat
    atk = base_stats[1].base_stat
    def_ = base_stats[2].base_stat
    spa = base_stats[3].base_stat
    spd = base_stats[4].base_stat
    spe = base_stats[5].base_stat
    pokemon_type = session.query(Pokemon_Types).filter_by(pokemon_id=id_)
    type_one = pokemon_type[0].type_id
    if pokemon_type.count() > 1:
        type_two = pokemon_type[1].type_id
    else:
        type_two = None
                  #id_, name, type_one, type_two, item, level, ability, hp, atk, def_, spa, spd, spe, ivs, g_max
    return Pokemon(id_, name, type_one, type_two, None, 0, None, hp, atk, def_, spa, spd, spe, None, g_max)

def parse_showdown_set(paste):
    #parse showdown set and return Pokemon class
    split_paste = paste.splitlines()  
    name = split_paste[0].split(" @ ")[0]
    if name.find('(M)') != -1 or name.find('(F)') != -1:
        name = name.replace(' (M)', '').replace(' (F)', '')
    if name.find("(") != -1:
        name = name[name.find("(")+1:name.find(")")]
    base_pokemon = get_pokemon(name)
    base_pokemon.item = split_paste[0].split(" @ ")[1].strip()
    base_pokemon.moves = []
    nature = 'Sassy'
    hp = '0'
    atk = '0'
    def_ = '0'
    spa = '0'
    spd = '0'
    spe = '0'
    for line in split_paste[1:]:
        line = line.strip()
        if line[:8] == "Ability:":
            base_pokemon.ability = line[9:]
        if line[:6] == "Level:":
            base_pokemon.level = int(line[7:])
        if line[:4] == "EVs:":
            ev_line_str = line[5:]
            for ev in ev_line_str.split(' / '):
                ev_stat = ev.split(' ')[0]
                ev_str = ev.split(' ')[1]
                match ev_str:
                    case 'HP':
                        hp = ev_stat
                    case 'Atk':
                        atk = ev_stat
                    case 'Def':
                        def_ = ev_stat
                    case 'SpA':
                        spa = ev_stat
                    case 'SpD':
                        spd = ev_stat
                    case 'Spe':
                        spe = ev_stat
        if line.split(" ")[1] == "Nature":
            nature = line.split(" ")[0].lower()
        if line[:4] == "IVs:":
            base_pokemon.ivs = line[5:].split(" / ")
        if line[:1] == "–" or line[:1] == "-":
            base_pokemon.moves.append(line[2:])
    evs = '/'.join([hp, atk, def_, spa, spd, spe])
    base_pokemon.spreads = [str(nature).title() + ':' + str(evs)]
    return base_pokemon

def get_smogon_meta():

    smogon_move_sets = []

    def convert_smogon_set(name, ability, item, spreads, moves):
        for spread in spreads:
            nature = spread.split(':')[0]
            evs = spread.split(':')[1].split('/')
            evs_str = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']
            evs_list = []
            for x in range(6):
                if evs[x] != '0':
                    evs_list.append(evs[x] + ' ' + evs_str[x])
            if evs_list == []:
                evs_list = None
            print(evs_list)

        #vars for Pokemon class:
        #(    id_, name, type_one, type_two, item, level, hp, atk, def_, spa, spd, spe, nature, ivs, evs)
        base_pokemon = get_pokemon(name)
        base_pokemon.level = 50
        base_pokemon.ability = ability
        base_pokemon.item = item
        #base_pokemon.nature = nature
        #base_pokemon.evs = evs_list
        base_pokemon.spreads = spreads
        base_pokemon.moves = moves
        #print(name, spread)
        smogon_move_sets.append(base_pokemon)
        #print(name, evs_list, moves)

    #Open Smogon Meta Usage data, parse sets and convert to a Python object
    with open('gen8vgc2022-1760.txt', 'r') as f:
        lines = f.read().replace('|', '').strip().splitlines()
        name = lines[1].strip()
        ability = ''
        item = ''
        #spread = ''
        spreads = []
        
        moves = []
        for x in range(len(lines)):
            line = lines[x].strip()
            try:
                #indicates if end of file
                next_line = lines[x+1].strip()
            except:
                #exception captures vars from last pokemon
                convert_smogon_set(name, ability, item, spreads, moves)
                break
            marker_check = line == '+----------------------------------------+'
            if marker_check and next_line == '+----------------------------------------+':
                convert_smogon_set(name, ability, item, spreads, moves)
                spreads = []
                moves = []
                name = lines[x+2].strip()
                #print(name)
            #Abilities
            if marker_check and next_line.startswith('Abilities'):
                ability = ''.join([i for i in lines[x+2] if not i.isdigit()]).replace('.', '').replace('%', '').strip()
            
            #Items
            if marker_check and next_line.startswith('Items'):
                item = ''.join([i for i in lines[x+2] if not i.isdigit()]).replace('.', '').replace('%', '').strip()
            
            #Spreads - EV & Nature
            if marker_check and next_line.startswith('Spreads'):
                spread_txt = lines[x+2:]
                for spread_line in spread_txt:
                    if spread_line.strip().strip().split(' ')[0] == 'Other': #'+----------------------------------------+':
                        break
                    else:
                        #print(name)
                        #print(spread_line.strip().split(' ')[0])
                        spreads.append(spread_line.strip().split(' ')[0])
                #print(lines[x+2:x+4])
                spread = lines[x+2].strip().split(' ')[0]
            
            #Moves
            if marker_check and next_line.startswith('Moves'):
                for m in range(10):
                    move_line = lines[x+2+m].strip()
                    if move_line == '+----------------------------------------+':
                        break
                    else:
                        move = ''.join([i for i in move_line if not i.isdigit()]).replace('.', '').replace('%', '').strip()
                        
                        if move != 'Nothing' and move != 'Other':
                            moves.append(move)
    return smogon_move_sets

def damage_calc(attacker, defender, opp_spread, move, user):

    if user == True:
        atk_spread = attacker.spreads[0]
        def_spread = opp_spread
    else:
        atk_spread = opp_spread
        def_spread = defender.spreads[0]

    atk_nature = parse_spread(atk_spread)[0]
    def_nature = parse_spread(def_spread)[0]

    type_eff = 1
    targets = 1 #how many targets, check move in db for targets
    weather = 1 #auto-set for abilities?
    critical = 1 #check move db
    burn = 1 #external setting
    random = 1 #or 0.85
    other = 1 #"other is 1 in most cases, and a different multiplier when specific interactions of moves, Abilities, or items take effect"

    move_name = move.replace("'", '').replace(' ', '-').lower()
    move = session.query(Moves).filter_by(identifier=move_name).first()
    multi_target_moves =[6, 9, 11, 12, 14]
    if move.target_id in multi_target_moves:
        targets = 0.75

    #check for fling - need to fix
    if move.power == None:
        move.power = 0

    #other weird moves to check:
    #Heat Crash
    #Heavy Slam
    #Gyro Ball
    #Metal Burst
    #Mirror Coat
    #Final Gambit
    #Low Kick

    #check if atk or spa or non-damaging
    if move.damage_class_id == 2:
        #atk
        atk_str = 'Atk'
        def_str = 'Def'
        atk_stat_id = 2
        def_stat_id = 3
    elif move.damage_class_id == 3:
        #spa
        atk_str = 'SpA'
        def_str = 'SpD'
        atk_stat_id = 4
        def_stat_id = 5
    else:
        #Non damaging move
        return 0, 0, 0, 0, 0, 0, ''

    #check stab
    if move.type_id == attacker.type_one or move.type_id == attacker.type_two:
        stab = 1.5
    elif attacker.ability == "Libero" or "Protean":
        #abilites that change users typing to match move typing
        stab = 1.5
    else:
        stab = 1

    #check if defender is multitype
    if defender.type_two != None:
        #multitype
        type_eff_one = session.query(Type_Efficacy).filter_by(damage_type_id=move.type_id).filter_by(target_type_id=defender.type_one).first()
        type_eff_two = session.query(Type_Efficacy).filter_by(damage_type_id=move.type_id).filter_by(target_type_id=defender.type_two).first()
        type_eff = (type_eff_one.damage_factor * 0.01) * (type_eff_two.damage_factor * 0.01)
    else:
        #single type
        type_eff = session.query(Type_Efficacy).filter_by(damage_type_id=move.type_id).filter_by(target_type_id=defender.type_one).first()
        type_eff = type_eff.damage_factor * 0.01
    #check for levitate    
    if defender.ability == 'Levitate' and move.type_id == 5:
        type_eff = 0
    if mew_mode == True:
        type_eff = 1

    #get true stat w/ iv, ev
    true_atk = get_true_stat(atk_stat_id, attacker, atk_spread)
    true_def = get_true_stat(def_stat_id, defender, def_spread)
    true_hp = get_true_stat(1, defender, def_spread)
    atk_vs_def = true_atk[0] / true_def[0]

    high_roll = floor(((((2 * attacker.level // 5) + 2) * move.power * atk_vs_def // 50) + 2) * targets * weather * critical * random * stab * type_eff * burn * other)
    random = 0.925
    med_roll = floor(((((2 * attacker.level // 5) + 2) * move.power * atk_vs_def // 50) + 2) * targets * weather * critical * random * stab * type_eff * burn * other)    
    random = 0.85
    low_roll = floor(((((2 * attacker.level // 5) + 2) * move.power * atk_vs_def // 50) + 2) * targets * weather * critical * random * stab * type_eff * burn * other)
    
    high_percent = round(high_roll / true_hp[0] * 100, 1)
    med_percent = round(med_roll / true_hp[0] * 100, 1)
    low_percent = round(low_roll / true_hp[0] * 100, 1)

    atk_true_spe = get_true_stat(6, attacker, atk_spread)
    def_true_spe = get_true_stat(6, defender, def_spread)

    result_str = (str(true_atk[1]) + '+', atk_str, attacker.name, move_name, 'vs.', str(true_hp[1]), 'HP /', str(true_def[1]) + '+', def_str, defender.name + ':', str(low_roll) + '-' + str(high_roll), '(' + str(low_percent), '-', str(high_percent) + '%)')
    result_str = ' '.join(result_str)
    
    return high_roll, med_roll, low_roll, high_percent, med_percent, low_percent, result_str, move_name, atk_str.lower(), attacker.name, atk_nature, str(true_atk[0]), defender.name, def_nature, str(true_hp[0]), str(true_def[0]), str(atk_true_spe[0]), str(def_true_spe[0]), str(user)

def get_user_team():
        user_team_list = []

        with open('team1.txt', 'r') as user_team:
                team = user_team.read()
                team = team.split('\n\n')
                if team[-1] == '\n':
                    team = team[:-1]
                for t in team:
                    mon = parse_showdown_set(t)
                    user_team_list.append(mon)
        return user_team_list

def write_to_file(calc_str, calc_list):
    with open('team_calc_results.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        csv_writer.writerow(calc_str)
        for calc in calc_list:
            csv_writer.writerow(calc)

def team_vs_team_calc(user_team, opp_team):
    calc_str = ['high_roll', 'med_roll', 'low_roll', 'high_percent', 'med_percent', 'low_percent', 'calc_str', 'move', 'atk_or_spa', 'attacker', 'atk_nature', 'true_atk', 'defender', 'def_nature', 'true_hp', 'true_def', 'atk_true_spe', 'def_true_spe', 'user']
    calc_list = []
    
    for user_mon in user_team:
        for opp_mon in opp_team:
            print(opp_mon.spreads)
            for spread in opp_mon.spreads:
                if only_strongest_moves == True:
                    best_move = [0, 0, 0, 0, 0, 0, '']
                    best_opp_move = [0, 0, 0, 0, 0, 0, '']
                    for move in user_mon.moves:
                        calc = damage_calc(user_mon, opp_mon, spread, move, True)
                        if float(calc[3]) > float(best_move[3]):
                            best_move = calc
                    for move in opp_mon.moves:
                        calc = damage_calc(opp_mon, user_mon, spread, move, False)
                        if float(calc[3]) > float(best_opp_move[3]):
                            best_opp_move = calc
                    if best_move not in calc_list:
                        calc_list.append(best_move)
                    if best_opp_move not in calc_list:
                        calc_list.append(best_opp_move)
                else:
                    for move in user_mon.moves:
                        calc = damage_calc(user_mon, opp_mon, spread, move, True)
                        if calc[6] != '' and calc not in calc_list:
                            calc_list.append(calc)
                    for move in opp_mon.moves:
                        calc = damage_calc(opp_mon, user_mon, spread, move, False)
                        if calc[6] != '' and calc not in calc_list:
                            calc_list.append(calc)
    write_to_file(calc_str, calc_list)

def get_speed_stats(user_team, opp_team):
    calc_str = ''
    pokemon_list = []
    for mon in user_team:
        true_spe = get_true_stat(6, mon)

#For an online competition where only stage 1 Pokemon were allowed.
"""
def get_tiny_tourney():
    not_in_swsh = [13, 16, 19, 21, 46, 48, 56, 69, 74, 88, 96, 100, 152, 155, 158, 161, 165, 167, 179, 187, 190, 191, 198, 200, 204, 209, 216, 218, 228, 231, 261, 265, 276, 283, 285, 287, 296, 299, 300, 307, 316, 322, 325, 331, 353, 366, 387, 390, 393, 396, 399, 401, 408, 410, 412, 418, 431, 433, 456, 489, 495, 498, 501, 504, 511, 513, 515, 522, 540, 580, 585, 602, 650, 653, 656, 664, 667, 669, 672, 731, 734, 739, 789]
    eligible_pokemon = session.query(Pokemon_DB).filter(Pokemon_DB.height <= 10)
    pokemon_list = []
    print(eligible_pokemon.count())
    for mon in eligible_pokemon:
        evo_by_id = session.query(Pokemon_Species).filter_by(id=mon.species_id).first()
        if evo_by_id != None:
            evolution_chain_id = evo_by_id.evolution_chain_id
            evolutions = session.query(Pokemon_Species).order_by(Pokemon_Species.order).filter_by(evolution_chain_id=evolution_chain_id)
            first_evo = evolutions.first()
            evo_count = evolutions.count()
            if evo_count > 1 and mon.species_id == first_evo.id and mon.species_id not in not_in_swsh:
                move_learn_set = session.query(Pokemon_Moves).filter(Pokemon_Moves.pokemon_id == mon.id, Pokemon_Moves.version_group_id == 20)
                mon = get_pokemon(mon.identifier)
                mon.level = 50
                for move in move_learn_set:
                    move = session.query(Moves).filter(Moves.id == move.move_id, Moves.damage_class_id != 1).first()
                    if move != None:
                        mon.moves.append(move.identifier)        
                pokemon_list.append(mon)
    print(pokemon_list)
    return pokemon_list        
"""

user_team = get_user_team()
opp_team = get_smogon_meta()

team_vs_team_calc(user_team, opp_team)