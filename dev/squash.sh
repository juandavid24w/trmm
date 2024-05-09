. venv/bin/activate

# If you reach the 1000th migration, this script doesn't work

app="$1"

if [ -z "$app" ]; then
  echo "Provide an app name!"
  exit
fi

tmpname=squashed_initial

last=$(ls -1 "$app"/migrations/0*.py | sort | tail -1 | cut -d_ -f 1 | cut -d/ -f3)
./manage.py squashmigrations "$app" "$last" --squashed-name $tmpname

mv "$app"/migrations/0*"$tmpname".py /tmp/$$.py
rm "$app"/migrations/0*.py
mv /tmp/$$.py "$app"/migrations/0001_initial.py
