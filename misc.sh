for file in *.svg; do rsvg-convert "$file" -o "pngs/${file%.svg}.png"; done

50 * * * * /home/hayden/EInk-Display/run.sh