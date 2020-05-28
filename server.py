#!/usr/bin/env python3

from aiohttp import web
import asyncio
import pyatv
import os

COMMANDS = {
    'turn_off': lambda atv: atv.power.turn_off(),
    'turn_on': lambda atv: atv.power.turn_on(),

    'right': lambda atv: atv.remote_control.right(),
    'left': lambda atv: atv.remote_control.left(),
    'down': lambda atv: atv.remote_control.down(),
    'up': lambda atv: atv.remote_control.up(),
    'menu': lambda atv: atv.remote_control.menu(),
    'top_menu': lambda atv: atv.remote_control.top_menu(),
    'home': lambda atv: atv.remote_control.home(),
    'home_hold': lambda atv: atv.remote_control.home_hold(),
    'select': lambda atv: atv.remote_control.select(),
    'pause': lambda atv: atv.remote_control.pause(),
    'play': lambda atv: atv.remote_control.play(),
    'playpause': lambda atv: atv.remote_control.play_pause(),
    'stop': lambda atv: atv.remote_control.stop(),
    'next': lambda atv: atv.remote_control.next(),
    'previous': lambda atv: atv.remote_control.previous(),
}

def create_atv_handler(atv):
    async def handler(request):
        command = request.match_info.get('command')
        if not command in COMMANDS:
            return web.Response(status=400, text='Unknown command')

        print('Running command: {}'.format(command))
        await COMMANDS[command](atv)
        return web.Response(text=command)
    
    return handler

async def connect_to_atv(loop):
    print("Scanning for AppleTVs...")
    devices = await pyatv.scan(loop, timeout=5)
    if not devices:
        raise Exception('No devices found!')

    print("Connecting to {}".format(devices[0].address))
    atv = await pyatv.connect(devices[0], loop)
    return atv

def main():
    # Connect to AppleTV.
    loop = asyncio.new_event_loop()
    atv = loop.run_until_complete(connect_to_atv(loop))

    # Server
    app = web.Application()
    app.router.add_get('/atv/{command}', create_atv_handler(atv))

    async def redirect_to_app(request):
        return web.HTTPFound(location='/web/index.html')
    app.router.add_get('/web', redirect_to_app)
    app.router.add_get('/web/', redirect_to_app)
    app.router.add_static('/web', path='public', follow_symlinks=True)

    port = os.getenv('PORT', 8080)
    web.run_app(app, port=port)

if __name__ == '__main__':
    main()

