import argparse
import json
import os
from random import choice, randint

command_file = "command.txt"
place_ship_file = "place.txt"
game_state_file = "state.json"
output_path = '.'
map_size = 0
round_now = 0
energy = 0

def can_shot(ships, Shiptype, Weapontype):
    # return true if we can perform double shot (the ship that required is still exist and energy available exceed the minimun requirement)
    # either, return false
    global energy
    for ship in ships:
        if (ship['ShipType'] == Shiptype):
            if (ship['Destroyed']):
                return False
            else:
                for shot in ship['Weapons']:
                    if (shot['WeaponType'] == Weapontype):
                        return (energy >= shot['EnergyRequired'])

def can_shot_koordinat(opponent_map, cells):
    # return true if all value of cells is not damaged, missed, dan ShieldHit
    # either, return false
    global map_size
    for cell in cells:
        if opponent_map[cell[0]*map_size + cell[1]]['Damaged'] or opponent_map[cell[0]*map_size + cell[1]]['ShieldHit'] or opponent_map[cell[0]*map_size + cell[1]]['Missed']:
            return False
    return True

def valid_koordinat(cells):
    # return true if x and y koordinat is in range of 0 and map_size
    # either, return false
    for p in cells:
        if not((p[0]>=0) and (p[1]>=0) and (p[0]<map_size) and (p[1]<map_size)):
            return False
    return True

def count_hit(opponent_map, cells):
    #this function return how many value in cells that is not damaged, shieldhit, and missied
    global map_size
    ret = 0
    for cell in cells:
        if not(opponent_map[cell[0]*map_size + cell[1]]['Damaged'] or opponent_map[cell[0]*map_size + cell[1]]['ShieldHit'] or opponent_map[cell[0]*map_size + cell[1]]['Missed']):
            ret += 1
    return ret

def cek_around(opponent_map, cells, keyword):
    # return true if the upside, downside, rigthside, and leftside off all value in cells hasnt keyword
    # keyword can be refere to damaged, missed, or shieldhit, depend on the paramater
    # either, return false
    global map_size
    for cell in cells:
        if valid_koordinat([cell]):
            if opponent_map[cell[0]*map_size + cell[1]][keyword]:
                return False
    return True

def main(player_key):
    # main progam, reading the .json file
    global map_size, round_now, energy
    # Retrieve current game state
    with open(os.path.join(output_path, game_state_file), 'r') as f_in:
        state = json.load(f_in)
    map_size = state['MapDimension']
    energy = state['PlayerMap']['Owner']['Energy']
    shield = state['PlayerMap']['Owner']['Shield']['Active']
    shield_charge = state['PlayerMap']['Owner']['Shield']['CurrentCharges']
    round_now = state['Round']
    ships_left = state['PlayerMap']['Owner']['ShipsRemaining']
    if (state['Phase'] == 1):
        # algorithm for placing ships
        place_ships()
    else:
        # algorithm for placing shield
        # shield is placed when there is only 1 remaining shield, shield hasn't activated, and shield_charge > 3
        if (ships_left == 1) and not(shield) and (shield_charge>1) :
            remaining_ship = state['PlayerMap']['Owner']['Ships']
            # searching for ship's coordinates that hasn't be damaged
            for ship in remaining_ship:
                if not(ship['Destroyed']):
                    for index in ship['Cells']:
                        if not(index['Hit']):
                            X = index['X']
                            Y = index['Y']
            output_shot(X, Y, 8)
        else:
            fire_shot(state['OpponentMap']['Cells'], state['PlayerMap']['Owner']['Ships'])


def output_shot(x, y, move):
    # move = 1  # 1=fire shot command code
    with open(os.path.join(output_path, command_file), 'w') as f_out:
        f_out.write('{},{},{}'.format(move, x, y))
        f_out.write('\n')
    pass

def fire_shot(opponent_map, ship):
    global round_now, energy, map_size
    # To send through a command please pass through the following <code>,<x>,<y>
    # Possible codes: 1 - Fireshot, 0 - Do Nothing (please pass through coordinates if
    #  code 1 is your choice)
    targets = []    # targets contain all cells that can be shot ( cells that hasnt be damaged, missed) and there is no missed cell around it
    all_target = []
    around_damaged = [] # around_damaged contain all cells that nearby damaged cells
    priority_target = [] # priority_target is the first cell in priority that has to be shot

    # iterate dan listing all targets, around_damaged, and priority_target
    for cell in opponent_map:
        if not cell['Damaged'] and not cell['Missed']:
            # algorithm for listing all the targets
            valid_cell = cell['X'], cell['Y']
            around = [[cell['X']+1, cell['Y']], [cell['X']-1, cell['Y']], [cell['X'], cell['Y']+1], [cell['X'], cell['Y']-1]]
            if cek_around(opponent_map, around, 'Missed'):
                targets.append(valid_cell)
            all_target.append(valid_cell)
        if cell['Damaged']:
            # algorithm for listing all around_damaged
            around = [[cell['X']+1, cell['Y']], [cell['X']-1, cell['Y']], [cell['X'], cell['Y']+1], [cell['X'], cell['Y']-1]]
            if cek_around(opponent_map, around, 'Damaged'):
                for place in around:
                    if valid_koordinat([place]):
                        p = opponent_map[place[0]*map_size+place[1]]
                        if not p['Damaged'] and not p['Missed']:
                            around_damaged.append(place)

    # algorithm for listing all priority_target
    for row in range(map_size):
        for col in range(map_size-1):
            if (opponent_map[row*map_size + col]['Damaged']) and (opponent_map[row*map_size + col + 1]['Damaged']):
                cellscek = [[row, col-1], [row, col+2]]
                for cell in cellscek:
                    if (valid_koordinat([cell]) and can_shot_koordinat(opponent_map, [cell])):
                        priority_target.append(cell)

    for col in range(map_size):
        for row in range(map_size-1):
            if (opponent_map[row*map_size + col]['Damaged']) and (opponent_map[(row+1)*map_size + col]['Damaged']):
                cellscek = [[row-1, col], [row+2, col]]
                for cell in cellscek:
                    if (valid_koordinat([cell]) and can_shot_koordinat(opponent_map, [cell])):
                        priority_target.append(cell)

    if (len(priority_target) > 0):
        # if it is not possible to shot with special shot, but there is a damaged cells in opponent map_size
        # it will shot in cells in the priority_target
        target = priority_target[randint(0,len(priority_target)-1)]
        action = 1
        output_shot(target[0], target[1], action)
        return

    if can_shot(ship, 'Submarine', 'SeekerMissile'):
        # algorithm for shot with SeekerMissile
        # algorithm will be explain in report document
        max = -1
        target = [0,0]
        for r in range(2,map_size-2):
            for c in range(2,map_size-2):
                cellscek = [ [r,c+2], [r-1,c+1], [r,c+1], [r+1,c+1],
                             [r-2,c], [r-1,c], [r,c], [r+1,c], [r+2,c],
                             [r-1,c-1], [r,c-1], [r+1,c-1], [r,c-2] ]
                # cellscek contain the coordinat that can be reach by the SeekerMissile
                count = count_hit(opponent_map, cellscek)
                if (count > max):
                    max = count
                    target = [r,c]
        action = 7
        output_shot(target[0], target[1], action)
        return

    if can_shot(ship, 'Battleship', 'DiagonalCrossShot'):
        # algorithm for searching where to shot the DiagonalCrossShot
        for cell in targets:
            shot_target = [ [cell[0]-1,cell[1]], [cell[0]+1,cell[1]], [cell[0],cell[1]+1], [cell[0], cell[1]-1], [cell[0], cell[1]] ]
            # check if rigthside, leftside, upside, downside the shot_target is not damaged
            if valid_koordinat(shot_target):
                if can_shot_koordinat(opponent_map, shot_target):
                    action = 6
                    output_shot(cell[0], cell[1], action)
                    return
            # check if rigthside, leftside, upside, downside the shot_target is not damaged
            shot_target = [ [cell[0]-1,cell[1]], [cell[0]+1,cell[1]], [cell[0],cell[1]+1], [cell[0], cell[1]-1] ]
            if valid_koordinat(shot_target):
                if can_shot_koordinat(opponent_map, shot_target):
                    action = 6
                    output_shot(cell[0], cell[1], action)
                    return
    if (len(around_damaged) > 0):
        # if it is not possible to shot with special shot, but there is a damaged cells in opponent map_size
        # it will shot near the damaged celss
        target = around_damaged[randint(0,len(around_damaged)-1)]
        action = 1
        output_shot(target[0], target[1], action)
        return

    # if we cant perform anyshot, we will random where to shot
    if (len(targets) > 0):
        target = targets[randint(0,len(targets)-1)]
    else:
        target = all_target[randint(0,len(all_target)-1)]

    action = 1
    output_shot(target[0], target[1], action)
    return

def place_ships():
    global map_size
    # Please place your ships in the following format <Shipname> <x> <y> <direction>
    # Ship names: Battleship(5), Cruiser(3), Carrier(5), Destroyer(2), Submarine(3)
    # Directions: north east south west
    if map_size < 7:
        ships = ['Battleship 0 0 east',
                 'Carrier 0 6 east',
                 'Cruiser 2 2 east',
                 'Destroyer 6 0 north',
                 'Submarine 6 6 south'
                 ]
    else:
        ships = ['Battleship 0 9 east',
                 'Carrier 9 5 north',
                 'Cruiser 0 4 south',
                 'Destroyer 8 0 east',
                 'Submarine 4 4 east'
                 ]

    with open(os.path.join(output_path, place_ship_file), 'w') as f_out:
        for ship in ships:
            f_out.write(ship)
            f_out.write('\n')
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PlayerKey', nargs='?', help='Player key registered in the game')
    parser.add_argument('WorkingDirectory', nargs='?', default=os.getcwd(), help='Directory for the current game files')
    args = parser.parse_args()
    assert (os.path.isdir(args.WorkingDirectory))
    output_path = args.WorkingDirectory
    main(args.PlayerKey)
