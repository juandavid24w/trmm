. ./venv/bin/activate
PYTHONPATH=venv/lib64/python3.11/site-packages/

for folder in . $(git submodule | sed 's/^.//' | cut -d' ' -f2)
do
  cd $folder
  files=$(
    git diff --diff-filter d --name-only \
    | cat - <(git diff --cached --name-only) \
    | cat - <(git ls-files --other --exclude-standard) \
    | egrep -v 'migrations/.*py$' \
  )
  htmlfiles=$(printf %s'\n' $files | egrep '.*.html$')
  pyfiles=$(printf %s'\n' $files | egrep '.*.py$')
  if [ -n "$htmlfiles" ]; then
    djhtml $htmlfiles 2>&1
  fi
  if [ -n "$pyfiles" ]; then
    darker $pyfiles -l 78 -W 8 -f -i --color -L "pylint"
  fi
  cd "$OLDPWD"
done
echo ' -------------'


