# Bruh Snake 🐍

A [Battlesnake](https://play.battlesnake.com) written in pure Python with no dependencies.

## Run it

```
python main.py
```

It listens on the `PORT` environment variable (default 8000).

## How it plays

- Never moves into walls or bodies. Tails that are about to move count as free.
- Flood-fills each possible move and avoids ones that leave less room than its own length.
- Stays away from the heads of equal-or-bigger snakes and goes for the heads of smaller ones.
- Eats when it's hungry or not the biggest snake; otherwise it circles near its own tail.

## Test it locally

```
python sim.py
```

This runs a small built-in simulator: Bruh Snake against random movers, and against copies of itself.

## Put it online

1. Import this repo into [Replit](https://replit.com) (or Render) and press Run to get a public URL.
2. Go to play.battlesnake.com → Account → Battlesnakes → Create, and paste in that URL.
3. Create a game, add the snake, and press Start.
