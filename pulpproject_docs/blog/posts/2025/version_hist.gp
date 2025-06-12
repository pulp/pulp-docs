reset
clear

set terminal png
set output "version_hist.png"

set title "Pulpcore versions released per month"
set timefmt "%Y-%m-%d"
set xdata time
set xtics format "%Y-%m" rotate by 330
set xrange ["2019-11-10":"2024-12-20"]
set style line 1 linecolor rgb "#347dbe"
set style line 2 linecolor rgb "#ff9507"
set style fill solid 1
set boxwidth 60*60*24*20

set arrow from "2023-04-16", graph 0 to "2023-04-16", graph 1 nohead linestyle 0

plot 'version_history.txt' u 3:(1.0) smooth frequency with boxes ls 2 title "Total versions",\
  '< grep -E "^[0-9]+\.[0-9]+\.0 " version_history.txt' u 3:(1.0) smooth frequency with boxes ls 1 title "Minor versions"
