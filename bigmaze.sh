#!/usr/bin/env sh

BOT1=MyBot.py
GREEDY=tools/sample_bots/python/GreedyBot.py
LEFTY=tools/sample_bots/python/LeftyBot.py
RANDOM=tools/sample_bots/python/RandomBot.py
#MAP=tools/maps/example/tutorial1.map
MAP=tools/maps/maze/cell_maze_p08_02.map
TURNS=1000

tools/playgame.py \
    --end_wait=0.25 \
    --verbose \
    --log_dir game_logs \
    --turns $TURNS \
    --map_file $MAP "$@" \
    -e \
    -O \
    "python $BOT1" \
    "python $RANDOM" \
    "python $RANDOM" \
    "python $RANDOM" \
    "python $RANDOM" \
    "python $RANDOM" \
    "python $RANDOM" \
    "python $RANDOM" \

