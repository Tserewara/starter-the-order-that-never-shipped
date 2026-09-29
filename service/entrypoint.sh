#!/bin/sh
# One image, two roles: `api` serves checkout, `worker` runs whatever works
# in the background.
case "$1" in
  api) exec python3 api.py ;;
  worker) exec python3 worker.py ;;
  *) exec "$@" ;;
esac
