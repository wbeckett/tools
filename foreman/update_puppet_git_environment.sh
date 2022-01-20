#!/bin/bash


CONFIG='/root/test/config'
source $CONFIG
SKIP_TAGS=()

function main {
  # Check Environmnet names provided. Should only contain letters
  environment_format

  # Pull repo into a temp directory
  TMP=$(  mktemp -d )
  cd $TMP

  git clone -b $BRANCH $REPO .

  # Check supplied TAGs
  for ENVIRONMENT in "${ENVIRONMENTS[@]}"; do
    TAG="TAG_${ENVIRONMENT}"
    tag_format "${!TAG}"
  done

  # Turn off advice about tags
  git config --global advice.detachedHead false


  # check out each tag and prep
  for ENVIRONMENT in "${ENVIRONMENTS[@]}"; do
    TAG="TAG_${ENVIRONMENT}"
    prep ${!TAG} $ENVIRONMENT
  done

  # Tags environments into place
  for ENVIRONMENT in "${ENVIRONMENTS[@]}"; do
    array_contains $ENVIRONMENT "${SKIP_TAGS[@]}" || shuffle $ENVIRONMENT
  done
}

######
# When we exit this will clean up any temporary data
function cleanup {
  echo "Cleaning up."

  if [ -d $TMP ]; then
    rm -rf ${TMP}
  else
    echo "$TMP does not exist"
    exit 1
  fi
}

######
# Check to see if an array contains a string
# https://stackoverflow.com/questions/3685970/check-if-a-bash-array-contains-a-value
function array_contains () {
    local seeking=$1; shift
    local in=1
    for element; do
        if [[ $element == "$seeking" ]]; then
            in=0
            break
        fi
    done
    return $in
}


######
#  Check to see if the TAG provided is in the correct format and exists in the repo
function tag_format {
  TAG=$1

  ######
  # Check to see if supplied tag is using correct format
  echo $TAG | egrep '^[0-9\.]+$' 2>&1 > /dev/null
  RET=$?
  if [ $RET -ne 0 ]; then
    echo "Incorrect tag format of $TAG"
    exit 1
  fi

  ######
  # Check to see if tag exists in the repo
  if [  ! $(git tag -l "$TAG") ]; then
    echo "TAG $TAG does not exist in repo"
    exit 1
  fi  
}


######
# Check that the enivornment is correctly formatted
function environment_format {

  for ENVIRONMENT in "${ENVIRONMENTS[@]}"; do
    echo $ENVIRONMENTS | egrep -i '^[a-z]+$' 2>&1 > /dev/null
    RET=$?
    if [ $RET -ne 0 ]; then
      echo "Incorrect repo format of $ENVIRONMENT"
      exit 1
    fi
  done

}


######
# Checkout each tag and copy the data into the staging area
# ${ENVS}/.${NAME} This later can be moved into its final location
function prep {
  TAG=$1
  NAME=$2
  SKIP=false

  # See if we have aleady in place the NAME/TAG

  if [ -f ${ENVS}/${NAME}/TAG ]; then
    T=$( cat ${ENVS}/${NAME}/TAG )

    if [ "X${T}" == "X${TAG}" ]; then
      echo "Tag: ${TAG} Already exists in ${NAME}. Skipping."
      SKIP_TAGS+=( $NAME )
      SKIP=true
    fi
  fi

  if [ $SKIP == false ]; then
    echo "Checking out tags/${TAG} for $NAME"
    git checkout tags/${TAG} 

    if [ ! -d ${ENVS}/.${NAME} ]; then
      mkdir -p ${ENVS}/.${NAME}
    fi 

    # Copy data into place and remove anythig not in the repo
    rsync -axr --delete --exclude=.git . ${ENVS}/.${NAME}/
    echo $TAG > ${ENVS}/.${NAME}/TAG

    # Check permissions are correct
    chmod 755 -R ${ENVS}/.${NAME}/
    restorecon -vR ${ENVS}/.${NAME}

  fi
}


#######
# Move the enviroment from its staging to final location.
function shuffle {
  NAME=$1
  echo "Shuffling for $NAME"

  if [ -d ${ENVS}/${NAME} ]; then
    mv ${ENVS}/${NAME} ${ENVS}/${NAME}.old
  fi

  mv ${ENVS}/.${NAME} ${ENVS}/${NAME}
  rm -rf ${ENVS}/${NAME}.old
}

trap cleanup EXIT
main
