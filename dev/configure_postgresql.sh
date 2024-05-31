host="$1"

set -a; . .env; set +a

cmds=(
  "create database $SQL_DATABASE;"
  "create user $SQL_USER with encrypted password '$SQL_PASSWORD';"
  "alter database $SQL_DATABASE owner to $SQL_USER;"
)

local_file=/tmp/$$.sql
remote_file=/tmp/$$.sql

printf "%s\n" ${cmds[@]} > "$local_file"
scp "$local_file" "${host}:${remote_file}"
ssh "$host" "su postgres -c 'psql -f ${remote_file}'"


