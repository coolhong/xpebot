#! ./bash

DSM_ACCOUNT="admin"
PYTHON_PATH="/usr/bin/python"
XPEBOT_MAIN="/volume1/homes/$DSM_ACCOUNT/xpebot/main.py"
XPEBOT_CFG_PATH="/volume1/homes/$DSM_ACCOUNT/xpebot/xpebot.cfg"

function ProcChk()
{
    PID=`/bin/ps | /bin/grep "python" | /bin/grep "main.py" | /usr/bin/awk '{print $1}'`
    if [ "$PID" ] ;  then
        printf "%16s : [36m[1mRunning[0m\n" "XPEnology Telegram BOT";
    else
        printf "%16s : [31m[1mStopped[0m\n" "XPEnology Telegram BOT";
    fi;
}

case "$1" in
start)
    echo "[36m[1mStarting XPEnology Telegram BOT...[0m"
    cd $TGPATH
    PID=`/bin/ps | /bin/grep "python" | /bin/grep "main.py" | /usr/bin/awk '{print $1}'`

    if [ $PID ]; then
        echo "XPEnology Telegram BOT Already Running"
        # exit 1
    else
        $PYTHON_PATH "$XPEBOT_MAIN" "$XPEBOT_CFG_PATH" &
        ProcChk
    fi
    ;;
stop)
    echo "XPEnology Telegram BOT safe stop Trying"

    PID=`/bin/ps | /bin/grep "python" | /bin/grep "main.py" | /usr/bin/awk '{print $1}'`

    if [ -z $PID ]; then
        echo "XPEnology Telegram BOT Already Stop"
        # exit 1
    else
        kill -9 $PID
    fi

    sleep 1
    ProcChk
    ;;
chk)
    ProcChk
    ;;
*)
    echo "Usage : `basename $0` [ start | stop | chk ]"
    ;;
esac
