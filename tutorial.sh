#!/usr/bin/env sh

BOT1=MyBot.py
BOT2=tools/sample_bots/python/GreedyBot.py
MAP=tools/maps/example/tutorial1.map
TURNS=500

tools/playgame.py \
    --end_wait=0.25 \
    --verbose \
    --log_dir game_logs \
    --turns $TURNS \
    --map_file $MAP "$@" \
    -e \
    -O \
    "python $BOT1" \
    "python $BOT2"
