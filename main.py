# /// script
# dependencies = [
#  "pygame-ce",
#  "pytmx",
# ]
# ///

if __name__ == '__main__':
    import asyncio
    import src.main
    import logging
    logging.basicConfig(level=logging.INFO)
    LOG = logging.getLogger(__name__)
    LOG.info('Creating Game object')
    game = src.main.Game()
    LOG.info('Launching game loop...')
    asyncio.run(game.run())
