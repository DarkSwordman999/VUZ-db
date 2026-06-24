#!/bin/bash

cd "$HOME/Desktop/DATA_BASE/VUZ/app" || exit 1

if [ ! -f "gui.py" ] && [ -f "gui.py." ]; then
    mv "gui.py." "gui.py"
fi

if [ ! -f "gui.py" ]; then
    echo "Не найден app/gui.py"
    exit 1
fi

python3 -m py_compile gui.py || exit 1
python3 gui.py
