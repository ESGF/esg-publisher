for file in $(ls /p/user_pub/publish-queue/CMIP6-maps-todo2 | head -n 10000)
do
  mv /p/user_pub/publish-queue/CMIP6-maps-todo2/$file /p/user_pub/publish-queue/CMIP6-maps-todo
done
