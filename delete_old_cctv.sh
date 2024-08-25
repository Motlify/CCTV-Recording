#!/bin/bash
MASTER_DIR=/mnt/cctv/recordings
DAYS_RETENTION=$1

# Scan dirs
for camera in "$MASTER_DIR"/* ; do
    for year_dir in "$camera"/* ; do
        for month_dir in "$year_dir"/* ; do
            if [ -d "$month_dir" ] ; then
                for day_dir in "$month_dir"/* ; do
                    if [ -d "$day_dir" ] ; then
                        full_date=$(echo "$day_dir" | cut -d '/' -f 6,7,8)
                        year=$(echo "$full_date" | cut -d '/' -f 1)
                        month=$(echo "$full_date" | cut -d '/' -f 2)
                        day=$(echo "$full_date" | cut -d '/' -f 3)
                        if [[ "$year" =~ ^[0-9][0-9][0-9][0-9]$ ]] && [[ "$month" =~ ^[0-9][0-9]$ ]] && [[ "$day" =~ ^[0-9][0-9]$ ]]; then
                            date=$(date -d "$year-$month-$day" '+%s')
                            today=$(date +%Y-%m-%d)
                            today=$(date -d "$today" '+%s')
                            diff=$(("$today"-"$date"))
                            diff_in_days=$(("$diff"/86400))
                            if [ $diff_in_days -gt $DAYS_RETENTION ] ; then
                                echo "Footage is $diff_in_days days old - deleting $day_dir"
                                rm -rf "$day_dir"
                            fi
                        fi
                    else
                        echo "Month is not existing - deleting $month_dir"
                        rm -rf "$month_dir"
                    fi
                done
            else
                echo "Year is not existing - deleting $month_dir"
                rm -rf "$month_dir"
            fi
        done
    done
done
