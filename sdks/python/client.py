#!/usr/bin/python

import sys
import json
import random
import heapq

if (sys.version_info > (3, 0)):
    print("Python 3.X detected")
    import socketserver as ss
else:
    print("Python 2.X detected")
    import SocketServer as ss


class NetworkHandler(ss.StreamRequestHandler):
    def handle(self):
        game = Game()

        while True:
            data = self.rfile.readline().decode() # reads until '\n' encountered
            json_data = json.loads(str(data))

            # uncomment the following line to see pretty-printed data
            # print(json.dumps(json_data, indent=4, sort_keys=True))

            time = json_data['time']
            turn = json_data['turn'] # get the current turn
            tile_updates = json_data['tile_updates']
            unit_updates = json_data['unit_updates']
            if turn == 0:
                game_info = json_data['game_info'] # get the game settings, only sent on turn 0

                # player_id = json_data['player_id']
                map_width = game_info['map_width']
                map_height = game_info['map_height']
                game_duration = game_info['game_duration']
                turn_duration = game_info['turn_duration']
                unit_info = game_info['unit_info']

                memory_map = [[[ ] for _ in range(map_height)] for _ in range(map_width)]
                my_units = unit_updates
                
                memory_map[my_units[0]['x']][my_units[0]['y']] = '[B]'
                base_location = (my_units[0]['x'], my_units[0]['y'])


            if time == 0:
                results = json_data['results']
                
                score = results['score']
                workers = results['workers']
                scouts = results['scouts']
                tanks = results['tanks']
                kills = results['kills']
                death = results['deaths']
                total_resources = results['total_resources']
                total_commands = results['total_commands']
                invalid_commands = results['invalid_commands']
                exploration_pct = results['exploration_pct']

                print(f"""
                Score: {score}
                Workers: {workers}
                Scouts: {scouts}
                Tanks: {tanks}
                Kills: {kills}
                Deaths: {death}
                Total Resources: {total_resources}
                Total Commands: {total_commands}
                Invalid Commands: {invalid_commands}
                Exploration Percentage: {exploration_pct}%
                """)
                return

            # update the tiles
            for tile in tile_updates:
                memory_map_x = tile['x']
                memory_map_y = tile['y']

                if not tile['visible']:
                    memory_map[memory_map_x][memory_map_y] = '[?]'
                elif tile['resources'] and tile['units']:
                    memory_map[memory_map_x][memory_map_y] = "[O]"
                elif tile['resources']:
                    memory_map[memory_map_x][memory_map_y] = "[R]"
                elif tile['units']:
                    memory_map[memory_map_x][memory_map_y] = "[E]"
                elif tile['blocked']:
                    memory_map[memory_map_x][memory_map_y] = "[X]"
                else:
                    memory_map[memory_map_x][memory_map_y] = "[ ]"

            for unit in unit_updates:
                if unit['status'] == 'dead':
                    my_units.remove(unit)
            
            # for row in memory_map:
            #     print(" ".join(map(str, row)))

            # response = game.get_random_move(json_data).encode()
            response = game.get_resource(json_data, memory_map, base_location).encode()
            self.wfile.write(response)



class Game:
    def __init__(self):
        self.units = set() # set of unique unit ids
        self.directions = ['N', 'S', 'E', 'W']

    def get_random_move(self, json_data):
        units = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])
        self.units |= units # add any additional ids we encounter
        unit = random.choice(tuple(self.units))
        direction = random.choice(self.directions)
        move = 'MOVE'
        command = {"commands": [{"command": move, "unit": unit, "dir": direction}]}
        response = json.dumps(command, separators=(',',':')) + '\n'
        return response

    def get_resource(self, json_data, memory_map, base_location):
        units = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])
        self.units |= units # add any additional ids we encounter

        unit = random.choice(tuple(self.units))
        direction = random.choice(self.directions)
        move = 'MOVE'

        resource = self.find_closest_unit_to_resource(json_data, memory_map)

        if resource[0]:
            unit = resource[0]
            closest_resource = resource[1]

            direction = self.get_move_direction(unit['x'], unit['y'], closest_resource[0], closest_resource[1])
            move = 'MOVE'

        for unit in json_data['unit_updates']:
            found_resouce = False

            if unit['type'] == 'base':
                continue
            unit_x = unit['x']
            unit_y = unit['y']

            if unit['resource'] == 10:
                move = 'MOVE'
                direction = direction = self.get_move_direction(unit['x'], unit['y'], base_location[0], base_location[1])
                command = {"commands": [{"command": move, "unit": unit["id"], "dir": direction}]}
                response = json.dumps(command, separators=(',',':')) + '\n'
                return response

            if memory_map[unit_x - 1][unit_y] == '[R]':
                found_resouce = True
                direction = 'W'
            elif memory_map[unit_x + 1][unit_y] == '[R]':
                found_resouce = True
                direction = 'E'
            elif memory_map[unit_x][unit_y + 1] == '[R]':
                found_resouce = True
                direction = 'S'
            elif memory_map[unit_x][unit_y - 1] == '[R]':
                found_resouce = True
                direction = 'N'
    
            if found_resouce:
                move = 'GATHER'
                command = {"commands": [{"command": move, "unit": unit['id'], "dir": direction}]}
                response = json.dumps(command, separators=(',',':')) + '\n'
                return response

        command = {"commands": [{"command": move, "unit": unit, "dir": direction}]}
        response = json.dumps(command, separators=(',',':')) + '\n'

        return response
    
    def find_closest_unit_to_resource(self, json_data, memory_map):
        closest_unit = None
        closest_resource = None
        min_distance = float('inf')

        for x in range(len(memory_map)):
            for y in range(len(memory_map[0])):
                if memory_map[x][y] == '[R]':
                    for unit in json_data['unit_updates']:
                        print(unit)
                        unit_x, unit_y = unit['x'], unit['y']
                        distance = abs(unit_x - x) + abs(unit_y - y)

                        if distance < min_distance:
                            min_distance = distance
                            closest_unit = unit
                            closest_resource = (x, y)
        return closest_unit, closest_resource
    
    def get_move_direction(self, current_x, current_y, target_x, target_y):
        if current_x < target_x:
            return 'E'  # Move East (right)
        elif current_x > target_x:
            return 'W'  # Move West (left)
        elif current_y < target_y:
            return 'S'  # Move South (down)
        elif current_y > target_y:
            return 'N'  # Move North (up)


if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '0.0.0.0'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
