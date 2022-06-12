# Disclaimer: This should not be used by anyone. It will likly break your instance of gitlab
# What does it do? It looks at the current version of gitlab and compiles a list of upgrades available
# and walks through each and every one of them.
# Usage: 
#   # bash plan.sh > upgrade.sh
#   Backup/snapshot your instance of gitlab
#   review upgrade.sh, ammend  and if brave
#   # bash upgrade.sh


GITLAB="gitlab-ce"
CURRENT=$( rpm -qa | grep ${GITLAB} )
LIST=$( dnf search ${GITLAB} --showduplicates | grep ${GITLAB}- | awk '{ print $1 }' | sort --version-sort -u )
MARK=false


echo "set -e"

# Run reconfigure before we upgrade to try and catching exisiting issues
echo "gitlab-ctl reconfigure"

for UPDATE in $LIST; do
  if $MARK ; then
    echo "# Upgrading to $UPDATE"
    echo "dnf install $UPDATE -y"
    echo "gitlab-ctl reconfigure"
    echo "gitlab-ctl restart"
    echo "sleep 30"
    echo "gitlab-ctl status"
    echo
    continue
  fi

  if [ $UPDATE == $CURRENT ]; then
    MARK=true
  fi
done
