todo=`ls /p/user_pub/publish-queue/CMIP6-maps-todo/ | wc -l | tr -d '\n'`
newerrs=0
echo $todo

while [[ $todo -gt 0 ]]
do
  errs=`ls /p/user_pub/publish-queue/CMIP6-maps-err/ | wc -l | tr -d '\n'`
  ls /p/user_pub/publish-queue/CMIP6-maps-todo/ | shuf -n 100 > maps-todo.txt
  cat maps-todo.txt | parallel --timeout 600 --jobs 16 bash publish.sh
  currenterrs=`ls /p/user_pub/publish-queue/CMIP6-maps-err/ | wc -l | tr -d '\n'`
  newerrs=$(( $currenterrs - $errs ))
  if [[ $newerrs -gt 50 ]]
  then
    echo "Too many errors"
    exit -1
  fi
  ls /p/user_pub/publish-queue/CMIP6-maps-todo | wc -l
  todo=`ls /p/user_pub/publish-queue/CMIP6-maps-todo/ | wc -l | tr -d '\n'`
done

if [[ $todo -eq 0 ]]
then
  echo "stale file handle issue, publisher stopped" 
  exit -1
fi
todo=`ls /p/user_pub/publish-queue/CMIP6-maps-todo/ | wc -l`
echo $todo
