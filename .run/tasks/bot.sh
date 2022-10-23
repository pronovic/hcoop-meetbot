# vim: set ft=bash sw=3 ts=3 expandtab:

help_bot() {
   echo "- run bot: Run a bot connected to an IRC server on localhost"
}

task_bot() {
   echo "Running the local bot..."

   if [ ! -d meetings ]; then
      mkdir -p meetings
   fi

   if [ ! -d localbot ]; then
      mkdir -p localbot/conf

      touch localbot/conf/channels.conf
      touch localbot/conf/ignores.conf
      touch localbot/conf/networks.conf
      touch localbot/conf/users.conf

      cat utils/localbot.conf.template | sed "s|%%WORKDIR%%|$(pwd)|" > localbot/localbot.conf
      cat utils/HcoopMeetbot.conf.template | sed "s|%%WORKDIR%%|$(pwd)|" > localbot/conf/HcoopMeetbot.conf
   fi

   poetry_run supybot localbot/localbot.conf
}

