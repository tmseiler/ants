#!/usr/bin/env sh

BOT1=MyBot.py
BOT2=tools/sample_bots/python/GreedyBot.py
#MAP=tools/maps/example/tutorial1.map
MAP=tools/maps/random_walk/random_walk_02p_01.map
TURNS=200

tools/playgame.py \
    --player_seed 42 \
    --end_wait=0.25 \
    --verbose \
    --nolaunch \
    --log_dir game_logs \
    --turns $TURNS \
    --map_file $MAP "$@" \
    -e \
    -O \
    "python $BOT1" \
    "python $BOT2"
