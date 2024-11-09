#!/usr/bin/python

import sys
import json
import random

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

                memory_map = [[[] for _ in range(map_height * 2 + 1)] for _ in range(map_width * 2 + 1)]
                my_units = unit_updates

                print('received width: ', map_width)
                print('received height: ', map_height)

                # for row in memory_map:
                #     print(" ".join(map(str, row)))

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
                memory_map_x = tile['x'] * 2 + 1
                memory_map_y = tile['y'] * 2 + 1

                memory_map[memory_map_x][memory_map_y] = tile
            
            for unit in unit_updates:
                if unit['status'] == 'dead':
                    my_units.remove(unit)

            response = game.get_random_move(json_data).encode()
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

    def get_goated_move(self, json_data):
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '0.0.0.0'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
